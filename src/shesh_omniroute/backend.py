"""Container backend — rootless podman preferred, docker accepted."""

from __future__ import annotations

import dataclasses
import shutil
import subprocess

from .config import Config


class BackendError(RuntimeError):
    pass


@dataclasses.dataclass
class Backend:
    """Thin wrapper over a container CLI. Never uses a shell; never logs keys."""

    binary: str

    def _run(self, *args: str, timeout: int = 120, capture: bool = True) -> subprocess.CompletedProcess:
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
                raise BackendError(f"container start failed: {proc.stderr.strip()[:300]}")
            return
        args = [
            "run", "-d",
            "--name", cfg.container_name,
            "--restart", "unless-stopped",
            "-p", f"127.0.0.1:{cfg.port}:20128",
            "-e", "OMNIROUTE_API_KEY=" + api_key,
            "-v", f"{cfg.config_dir}:/data:Z" if self.binary.endswith("podman") else f"{cfg.config_dir}:/data",
            cfg.image,
        ]
        proc = self._run(*args, timeout=180)
        if proc.returncode != 0:
            raise BackendError(f"container run failed: {proc.stderr.strip()[:300]}")

    def stop(self, cfg: Config) -> None:
        if self.exists(cfg.container_name):
            proc = self._run("stop", cfg.container_name, timeout=60)
            if proc.returncode != 0:
                raise BackendError(f"container stop failed: {proc.stderr.strip()[:300]}")

    def logs(self, cfg: Config, tail: int = 100) -> str:
        proc = self._run("logs", "--tail", str(tail), cfg.container_name, timeout=30)
        if proc.returncode != 0:
            raise BackendError(f"container logs failed: {proc.stderr.strip()[:300]}")
        return proc.stdout

    def image_present(self, image: str) -> bool:
        proc = self._run("image", "inspect", image, timeout=30)
        return proc.returncode == 0

    def build(self, containerfile: str, tag: str, context: str, timeout: int = 1800) -> None:
        proc = self._run("build", "-f", containerfile, "-t", tag, context, timeout=timeout, capture=True)
        if proc.returncode != 0:
            raise BackendError(f"image build failed: {proc.stderr.strip()[-500:]}")


def detect_backend(which=shutil.which) -> Backend | None:
    """Rootless podman first (CachyOS default), then docker."""
    for candidate in ("podman", "docker"):
        path = which(candidate)
        if path:
            return Backend(binary=path)
    return None
