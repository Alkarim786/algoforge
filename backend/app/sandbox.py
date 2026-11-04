"""Runs untrusted code in a throwaway, locked-down Docker container. User code never runs in this process."""
import json
import subprocess
import uuid
from dataclasses import dataclass

from app.config import settings

IMAGES = {"python": settings.sandbox_python_image}
MEMORY_LIMIT_MB = 256
# Leaves room for the harness and its copy of the inputs on top of the user process's limit.
CONTAINER_MEMORY = "384m"
CASE_OVERHEAD_SECONDS = 1
MAX_CONTAINER_SECONDS = 240
OOM_EXIT_CODE = 137


class SandboxError(Exception):
    """The platform failed. Says nothing about the user's code."""


class SandboxKilled(Exception):
    """The container's memory limit killed the harness, which only the user's code can cause."""


@dataclass
class CaseRun:
    outcome: str  # ok | tle | runtime_error
    stdout: str
    stderr: str
    runtime_ms: int
    memory_kb: int


def docker_command(image: str, name: str) -> list[str]:
    runtime = ["--runtime", settings.sandbox_runtime] if settings.sandbox_runtime else []
    return [
        "docker", "run", "--rm", "-i",
        *runtime,
        "--name", name,
        "--network", "none",
        "--memory", CONTAINER_MEMORY,
        "--memory-swap", CONTAINER_MEMORY,
        "--cpus", "1",
        "--pids-limit", "128",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
        "--ipc", "none",
        "--cap-drop", "ALL",
        "--cap-add", "SETUID",
        "--cap-add", "SETGID",
        "--security-opt", "no-new-privileges",
        "--log-driver", "none",
        image,
    ]  # fmt: skip


def run_code(language: str, code: str, inputs: list[str]) -> list[CaseRun]:
    """Returns one CaseRun per input, stopping early after a time limit is hit."""
    time_limit = settings.sandbox_time_limit_seconds
    payload = json.dumps(
        {"code": code, "inputs": inputs, "time_limit": time_limit, "memory_limit_mb": MEMORY_LIMIT_MB}
    )
    timeout = min(MAX_CONTAINER_SECONDS, 15 + len(inputs) * (time_limit * 2 + CASE_OVERHEAD_SECONDS))
    name = f"algoforge-sandbox-{uuid.uuid4().hex}"
    try:
        completed = subprocess.run(
            docker_command(IMAGES[language], name), input=payload.encode(), capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as error:
        raise SandboxError(f"container exceeded {timeout}s") from error
    finally:
        # Killing the docker client doesn't stop the container, so this is the actual hard kill.
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)

    if completed.returncode == OOM_EXIT_CODE:
        raise SandboxKilled
    if completed.returncode != 0:
        raise SandboxError(f"exit {completed.returncode}: {completed.stderr[-500:].decode(errors='replace')}")
    try:
        return [CaseRun(**result) for result in json.loads(completed.stdout)]
    except (ValueError, TypeError) as error:
        raise SandboxError("harness produced unreadable output") from error
