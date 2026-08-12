"""shesh-omniroute CLI — start/stop/status/logs/build."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backend import BackendError, detect_backend
from .config import load_config
from .health import probe, wait_healthy

ROOT = Path(__file__).resolve().parents[2]


def _status_text(cfg) -> str:
    backend = detect_backend()
    lines = [f"endpoint: {cfg.base_url}"]
    if backend is None:
        lines.append("backend: NONE (install podman or docker)")
    else:
        running = backend.is_running(cfg.container_name)
        lines.append(f"backend: {backend.binary} container={cfg.container_name} running={running}")
    lines.append(f"health: {'up' if probe(cfg.base_url) else 'down'}")
    lines.append(f"api key: {'set' if cfg.api_key() else 'missing'} (at {cfg.api_key_path})")
    lines.append(f"export SHESH_OMNIROUTE_BASE_URL={cfg.base_url}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="shesh-omniroute", description="Run the OmniRoute gateway for Shesh")
    ap.add_argument("command", choices=["start", "stop", "restart", "status", "logs", "build", "print-env"])
    ap.add_argument("--tail", type=int, default=100)
    ap.add_argument("--wait", type=float, default=60.0)
    args = ap.parse_args(argv)

    cfg = load_config()

    if args.command == "print-env":
        print(f"export SHESH_OMNIROUTE_BASE_URL={cfg.base_url}")
        key = cfg.api_key()
        if key:
            print("export SHESH_OMNIROUTE_API_KEY=$(cat ~/.config/shesh/omniroute/api.key)")
        return 0

    if args.command == "status":
        print(_status_text(cfg))
        return 0

    backend = detect_backend()
    if backend is None:
        print("error: no container backend (podman/docker) found on PATH", file=sys.stderr)
        return 2

    try:
        if args.command == "build":
            containerfile = ROOT / "Containerfile"
            backend.build(str(containerfile), cfg.image, str(ROOT))
            print(f"built {cfg.image}")
            return 0
        if args.command == "stop":
            backend.stop(cfg)
            cfg.write_state(running=False)
            print("stopped")
            return 0
        if args.command == "restart":
            backend.stop(cfg)
        if args.command in ("start", "restart"):
            key = cfg.ensure_api_key()
            if not backend.image_present(cfg.image):
                print(f"image {cfg.image} missing — build first: shesh-omniroute build", file=sys.stderr)
                return 3
            backend.start(cfg, key)
            if wait_healthy(cfg.base_url, timeout=args.wait):
                cfg.write_state(running=True)
                print(f"up: {cfg.base_url}")
                return 0
            print("container started but health probe timed out; check: shesh-omniroute logs", file=sys.stderr)
            return 4
        if args.command == "logs":
            print(backend.logs(cfg, tail=args.tail))
            return 0
    except BackendError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
