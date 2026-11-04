"""Attacks the real sandbox. Needs Docker, so run from the worker: docker compose exec worker pytest"""
import subprocess

import pytest

from app.sandbox import SandboxKilled, run_code

docker_available = subprocess.run(["docker", "info"], capture_output=True).returncode == 0
pytestmark = pytest.mark.skipif(not docker_available, reason="needs the Docker socket; run in the worker container")


def run_one(code, stdin=""):
    return run_code("python", code, [stdin])[0]


def test_runs_code_with_stdin_and_reports_usage():
    run = run_one("print(int(input()) * 2)", "21")
    assert run.outcome == "ok"
    assert run.stdout.strip() == "42"
    assert run.memory_kb > 0


def test_large_input_and_output_round_trip():
    payload = " ".join(["7"] * 200_000)
    run = run_one("print(len(input().split()))", payload)
    assert run.stdout.strip() == "200000"


def test_runtime_error_captures_stderr():
    run = run_one("raise ValueError('boom')")
    assert run.outcome == "runtime_error"
    assert "boom" in run.stderr


def test_infinite_loop_is_tle_and_stops_later_cases():
    runs = run_code("python", "while True: pass", ["1", "2", "3"])
    assert [run.outcome for run in runs] == ["tle"]


def test_sleeping_forever_is_tle():
    assert run_one("import time; time.sleep(600)").outcome == "tle"


def test_ignoring_cpu_signal_is_still_killed():
    code = "import signal\nsignal.signal(signal.SIGXCPU, signal.SIG_IGN)\nwhile True: pass"
    assert run_one(code).outcome == "tle"


def test_memory_limit():
    run = run_one("x = bytearray(1024 * 1024 * 1024)\nprint('allocated')")
    assert run.outcome == "runtime_error"
    assert "MemoryError" in run.stderr


def test_network_is_unreachable():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=1)\n"
        "    print('connected')\n"
        "except OSError:\n"
        "    print('blocked')\n"
    )
    assert run_one(code).stdout.strip() == "blocked"


@pytest.mark.parametrize("path", ["/harness/harness.py", "/etc/passwd", "/usr/local/bin/python3", "/tmp/main.py"])
def test_filesystem_is_not_writable(path):
    code = f"try:\n    open({path!r}, 'a')\n    print('wrote')\nexcept OSError:\n    print('blocked')\n"
    assert run_one(code).stdout.strip() == "blocked"


@pytest.mark.parametrize("path", ["/proc/1/environ", "/proc/1/mem", "/proc/1/fd/0", "/proc/1/fd/1"])
def test_harness_process_is_out_of_reach(path):
    code = f"try:\n    open({path!r}, 'rb+')\n    print('opened')\nexcept OSError:\n    print('blocked')\n"
    assert run_one(code).stdout.strip() == "blocked"


def test_cannot_regain_root():
    code = "import os\ntry:\n    os.setuid(0)\n    print('root')\nexcept OSError:\n    print(os.getuid())\n"
    assert run_one(code).stdout.strip() == "1000"


def test_fork_bomb_is_contained():
    code = (
        "import os\n"
        "while True:\n"
        "    try:\n"
        "        os.fork()\n"
        "    except OSError:\n"
        "        pass\n"
    )
    runs = run_code("python", code, ["1"])
    assert runs[0].outcome in ("tle", "runtime_error")
    # The sandbox itself survived, and the next submission is unaffected.
    assert run_one("print('alive')").stdout.strip() == "alive"


def test_output_flood_is_cut_off():
    run = run_one("while True: print('x' * 1000)")
    assert run.outcome == "runtime_error"
    assert "Output limit" in run.stderr
    assert len(run.stdout) <= 1024 * 1024


def test_background_process_cannot_see_later_cases():
    # Case 1 leaves a daemon that tries to steal case 2's stdin; case 2 checks whether it survived.
    code = """
import os, sys, time, glob
line = input()
if line == "first":
    if os.fork() == 0:
        os.setsid()
        open("/tmp/daemon_ran", "w").close()
        time.sleep(30)
        os._exit(0)
    print("ok")
else:
    others = [p for p in glob.glob("/proc/[0-9]*") if os.path.basename(p) not in ("1", str(os.getpid()))]
    alive = [p for p in others if os.stat(p).st_uid == 1000]
    print(len(alive), os.path.exists("/tmp/daemon_ran"))
"""
    runs = run_code("python", code, ["first", "second"])
    assert runs[1].stdout.split() == ["0", "False"]


def test_process_exit_with_open_pipes_does_not_hang():
    code = "import os, time\nif os.fork() == 0:\n    time.sleep(30)\nelse:\n    print('done')\n"
    run = run_one(code)
    assert run.outcome == "ok"
    assert run.stdout.strip() == "done"


def test_exhausting_container_memory_reports_killed_or_runtime_error():
    code = (
        "import os\n"
        "for _ in range(6):\n"
        "    if os.fork() == 0:\n"
        "        break\n"
        "x = bytearray(200 * 1024 * 1024)\n"
        "for i in range(0, len(x), 4096):\n"
        "    x[i] = 1\n"
        "import time; time.sleep(3)\n"
    )
    try:
        runs = run_code("python", code, ["1"])
        assert runs[0].outcome in ("tle", "runtime_error", "ok")
    except SandboxKilled:
        pass
    assert run_one("print('alive')").stdout.strip() == "alive"
