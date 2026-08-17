"""Container backend — rootless podman preferred, docker accepted."""

from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import ClassVar

from .config import Config

# Operation labels for BackendError — centralized so raise sites carry no
# message strings (TRY003) and the excerpt policy below stays keyed by them.
OP_START = "container start"
OP_RUN = "container run"
OP_STOP = "container stop"
OP_LOGS = "container logs"
OP_BUILD = "image build"


class BackendError(RuntimeError):
    """A container-backend CLI operation failed.

    The message is constructed here — not at the raise site — so the stderr
    excerpt policy lives in exactly one place, and a None stderr can no
    longer crash the error path itself.
    """

    #: stderr excerpt policy per operation: (keep_tail, char_limit).
    #: Short-lived ops show the head; builds fail at the tail of the log.
    EXCERPT_POLICY: ClassVar[dict[str, tuple[bool, int]]] = {
        OP_START: (False, 300),
        OP_RUN: (False, 300),
        OP_STOP: (False, 300),
        OP_LOGS: (False, 300),
        OP_BUILD: (True, 500),
    }

    def __init__(self, operation: str, stderr: str | None) -> None:
        self.operation = operation
        tail, limit = self.EXCERPT_POLICY.get(operation, (False, 300))
        excerpt = (stderr or "").strip()
        excerpt = excerpt[-limit:] if tail else excerpt[:limit]
        super().__init__(f"{operation} failed: {excerpt}")


@dataclasses.dataclass
class Backend:
    """Thin wrapper over a container CLI. Never uses a shell; never logs keys."""

    binary: str

    def _run(self, *args: str, timeout: int = 120,
             capture: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            [self.binary, *args],
            capture_output=capture,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc

    def exists(self, name: str) -> bool:
        proc = self._run("container", "inspect", name, timeout=30)
        return proc.returncode == 0

    def is_running(self, name: str) -> bool:
        proc = self._run("container", "inspect", "-f", "{{.State.Running}}", name, timeout=30)
        return proc.returncode == 0 and proc.stdout.strip() == "true"

    def start(self, cfg: Config, api_key: str) -> None:
        """Start (or start-and-create) the gateway container."""
        if self.exists(cfg.container_name):
            proc = self._run("start", cfg.container_name, timeout=120, capture=True)
            if proc.returncode != 0 and "already running" not in (proc.stderr or "").lower():
                raise BackendError(OP_START, proc.stderr)
            return
        env_dir = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
        env_dir.mkdir(parents=True, exist_ok=True)
        fd, env_path = tempfile.mkstemp(prefix="shesh-omniroute-", dir=env_dir, text=True)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("OMNIROUTE_API_KEY=" + api_key + "\n")
            args = [
                "run", "-d",
                "--name", cfg.container_name,
                "--restart", "unless-stopped",
                "-p", f"127.0.0.1:{cfg.port}:20128",
                "--env-file", env_path,
                "-v", (f"{cfg.config_dir}:/data:Z" if self.binary.endswith("podman")
                       else f"{cfg.config_dir}:/data"),
                cfg.image,
            ]
            proc = self._run(*args, timeout=180)
            if proc.returncode != 0:
                raise BackendError(OP_RUN, proc.stderr)
        finally:
            try:
                os.unlink(env_path)
            except FileNotFoundError:
                pass

    def stop(self, cfg: Config) -> None:
        if self.exists(cfg.container_name):
            proc = self._run("stop", cfg.container_name, timeout=60)
            if proc.returncode != 0:
                raise BackendError(OP_STOP, proc.stderr)

    def logs(self, cfg: Config, tail: int = 100) -> str:
        proc = self._run("logs", "--tail", str(tail), cfg.container_name, timeout=30)
        if proc.returncode != 0:
            raise BackendError(OP_LOGS, proc.stderr)
        return proc.stdout

    def image_present(self, image: str) -> bool:
        proc = self._run("image", "inspect", image, timeout=30)
        return proc.returncode == 0

    def build(self, containerfile: str, tag: str, context: str, timeout: int = 1800) -> None:
        proc = self._run("build", "-f", containerfile, "-t", tag, context,
                         timeout=timeout, capture=True)
        if proc.returncode != 0:
            raise BackendError(OP_BUILD, proc.stderr)


def detect_backend(which=shutil.which) -> Backend | None:
    """Rootless podman first (CachyOS default), then docker."""
    for candidate in ("podman", "docker"):
        path = which(candidate)
        if path:
            return Backend(binary=path)
    return None
