"""Runs inside the sandbox container as root (with only CAP_SETUID and CAP_SETGID).

Reads {code, inputs, time_limit, memory_limit_mb} from stdin and prints a JSON list of per-case
results. User code runs as an unprivileged uid, so it can't read this process's memory (which holds
every case's input) or write to the real stdout. Everything that uid left behind is wiped between
cases, so one case can't observe another case's input.
"""
import json
import os
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import time

SANDBOX_UID = 1000
CODE_PATH = "/tmp/main.py"
MAX_STDOUT = 1024 * 1024
MAX_STDERR = 64 * 1024
WALL_LIMIT_FACTOR = 2
READ_CHUNK = 65536


def drop_privileges() -> None:
    os.setgroups([])
    os.setgid(SANDBOX_UID)
    os.setuid(SANDBOX_UID)


def sweep() -> None:
    """Kill every process of the sandbox uid and delete its files, from a helper running as that uid."""
    pid = os.fork()
    if pid:
        os.waitpid(pid, 0)
        return
    try:
        drop_privileges()
        try:
            os.kill(-1, signal.SIGKILL)
        except ProcessLookupError:
            pass
        for entry in os.scandir("/tmp"):
            if entry.path != CODE_PATH:
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path, ignore_errors=True)
                else:
                    try:
                        os.unlink(entry.path)
                    except OSError:
                        pass
    finally:
        os._exit(0)


def run_case(stdin: str, time_limit: int, memory_limit_mb: int) -> dict:
    def prepare_child() -> None:
        memory = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (time_limit, time_limit + 1))
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        drop_privileges()

    process = subprocess.Popen(
        ["python3", "-B", "-I", CODE_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/tmp",
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "PYTHONUNBUFFERED": "1"},
        preexec_fn=prepare_child,
        start_new_session=True,
    )

    selector = selectors.DefaultSelector()
    pending_input = stdin.encode()
    os.set_blocking(process.stdin.fileno(), False)
    selector.register(process.stdin, selectors.EVENT_WRITE)
    stdout, stderr = bytearray(), bytearray()
    selector.register(process.stdout, selectors.EVENT_READ, (stdout, MAX_STDOUT))
    selector.register(process.stderr, selectors.EVENT_READ, (stderr, MAX_STDERR))

    def pump(timeout: float) -> bool:
        """Move pending data. Returns True once an output stream goes over its cap."""
        nonlocal pending_input
        for key, _ in selector.select(timeout):
            if key.fileobj is process.stdin:
                try:
                    written = os.write(key.fd, pending_input[:READ_CHUNK])
                    pending_input = pending_input[written:]
                except BrokenPipeError:
                    pending_input = b""
                if not pending_input:
                    selector.unregister(process.stdin)
                    process.stdin.close()
                continue
            chunk = os.read(key.fd, READ_CHUNK)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            buffer, limit = key.data
            buffer += chunk
            if len(buffer) > limit:
                return True
        return False

    if not pending_input:
        selector.unregister(process.stdin)
        process.stdin.close()

    deadline = time.monotonic() + time_limit * WALL_LIMIT_FACTOR
    wait_result = None
    timed_out = output_exceeded = False
    while wait_result is None:
        if time.monotonic() >= deadline:
            timed_out = True
            break
        if selector.get_map():
            output_exceeded = pump(0.02)
        else:
            time.sleep(0.01)
        if output_exceeded:
            break
        pid, status, usage = os.wait4(process.pid, os.WNOHANG)
        if pid:
            wait_result = (status, usage)

    if wait_result is not None:
        # The process is gone; collect what it wrote. A leftover background process can't stall this.
        while selector.get_map():
            output_exceeded = pump(0) or output_exceeded
            if not selector.select(0):
                break

    sweep()
    if wait_result is None:
        _, status, usage = os.wait4(process.pid, 0)
        wait_result = (status, usage)
    # As PID 1 this process inherits orphans. Left unreaped, they'd use up the pid limit for later cases.
    try:
        while True:
            os.waitpid(-1, 0)
    except ChildProcessError:
        pass
    selector.close()

    status, usage = wait_result
    exit_code = os.waitstatus_to_exitcode(status)
    cpu_seconds = usage.ru_utime + usage.ru_stime
    killed_for_cpu = exit_code in (-signal.SIGXCPU, -signal.SIGKILL) and cpu_seconds >= time_limit

    if timed_out or killed_for_cpu:
        outcome = "tle"
    elif output_exceeded or exit_code != 0:
        outcome = "runtime_error"
    else:
        outcome = "ok"

    error_text = bytes(stderr[:MAX_STDERR]).decode(errors="replace")
    if output_exceeded:
        error_text += "\nOutput limit exceeded."
    elif outcome == "runtime_error" and exit_code < 0:
        error_text += f"\nProcess killed by {signal.Signals(-exit_code).name}."

    return {
        "outcome": outcome,
        "stdout": bytes(stdout[:MAX_STDOUT]).decode(errors="replace"),
        "stderr": error_text,
        "runtime_ms": round(cpu_seconds * 1000),
        "memory_kb": usage.ru_maxrss,
    }


def main() -> None:
    payload = json.load(sys.stdin)
    fd = os.open(CODE_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w") as file:
        file.write(payload["code"])

    results = []
    for case_input in payload["inputs"]:
        result = run_case(case_input, payload["time_limit"], payload["memory_limit_mb"])
        results.append(result)
        if result["outcome"] == "tle":  # Remaining cases can't change the verdict; don't spend their time.
            break
    json.dump(results, sys.stdout)


if __name__ == "__main__":
    main()
