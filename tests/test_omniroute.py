"""Offline test suite for the shesh-omniroute wrapper."""

from __future__ import annotations

import http.server
import os
import stat
import threading

import pytest

from shesh_omniroute.backend import Backend, BackendError, detect_backend
from shesh_omniroute.cli import main
from shesh_omniroute.config import Config, load_config
from shesh_omniroute.health import probe, wait_healthy


@pytest.fixture
def cfg(tmp_path):
    c = Config()
    c.config_dir = tmp_path
    return c


class TestConfig:
    def test_api_key_created_once_0600(self, cfg):
        key = cfg.ensure_api_key()
        assert key.startswith("sk-shesh-") and len(key) > 20
        mode = stat.S_IMODE(os.stat(cfg.api_key_path).st_mode)
        assert mode == 0o600
        assert cfg.ensure_api_key() == key  # stable

    def test_env_port_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SHESH_OMNIROUTE_PORT", "29999")
        c = load_config(config_dir=tmp_path)
        assert c.port == 29999
        assert c.base_url == "http://localhost:29999/v1"

    def test_state_roundtrip(self, cfg):
        cfg.write_state(running=True)
        assert cfg.read_state()["container"] == "shesh-omniroute"
        assert cfg.read_state()["running"] is True


class FakeBackend(Backend):
    def __init__(self, running=False, rc=0, stderr=""):
        super().__init__(binary="/usr/bin/podman")
        self.calls: list[tuple[str, ...]] = []
        self._running = running
        self._rc = rc
        self._stderr = stderr

    def _run(self, *args, timeout=120, capture=True):
        import subprocess

        self.calls.append(args)
        out = "true" if args[0:2] == ("container", "inspect") and self._running else ""
        return subprocess.CompletedProcess(args, self._rc if args[0] != "container" or self._running else 1, out, self._stderr)


class TestBackend:
    def test_detect_prefers_podman(self):
        b = detect_backend(which=lambda name: f"/usr/bin/{name}" if name == "podman" else None)
        assert b is not None and b.binary.endswith("podman")

    def test_detect_none(self):
        assert detect_backend(which=lambda name: None) is None

    def test_run_args_no_shell_key_only_in_env(self, cfg):
        fb = FakeBackend(rc=0)
        fb.start(cfg, "sk-test-key")
        run_call = next(c for c in fb.calls if c[0] == "run")
        assert "--name" in run_call and "shesh-omniroute" in run_call
        assert "OMNIROUTE_API_KEY=sk-test-key" in run_call
        assert any(a.endswith(":/data:Z") for a in run_call), "podman needs :Z for selinux/fuse mounts"
        assert any("127.0.0.1" in a for a in run_call), "port bound to localhost only"

    def test_start_failure_raises(self, cfg):
        fb = FakeBackend(rc=1, stderr="boom")
        with pytest.raises(BackendError):
            fb.start(cfg, "sk-x")

    def test_existing_container_started_not_recreated(self, cfg):
        fb = FakeBackend(running=True)
        fb.start(cfg, "sk-x")
        assert any(c[:2] == ("start", "shesh-omniroute") for c in fb.calls)
        assert not any(c[0] == "run" for c in fb.calls)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(401)
        self.end_headers()

    def log_message(self, *a):
        pass


class _ClosedHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass


class TestHealth:
    def test_probe_counts_401_as_up(self):
        srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        assert probe(f"http://127.0.0.1:{port}/v1") is True
        srv.shutdown()
        srv.server_close()  # release the listening socket; shutdown() alone leaves it open

    def test_probe_down(self):
        assert probe("http://127.0.0.1:9/v1", timeout=0.5) is False

    def test_wait_healthy_uses_fake_clock(self, monkeypatch):
        ticks = iter([0.0, 0.5, 1.0, 2.0, 61.0])
        monkeypatch.setattr("shesh_omniroute.health.probe", lambda url: False)
        ok = wait_healthy("http://x", timeout=60.0, interval=1.0,
                          sleep=lambda s: None, now=lambda: next(ticks))
        assert ok is False


class TestCLI:
    def test_print_env(self, cfg, monkeypatch, capsys):
        monkeypatch.setenv("SHESH_OMNIROUTE_PORT", "20128")
        monkeypatch.setattr("shesh_omniroute.cli.load_config", lambda: cfg)
        assert main(["print-env"]) == 0
        out = capsys.readouterr().out
        assert "SHESH_OMNIROUTE_BASE_URL=http://localhost:20128/v1" in out

    def test_status_without_backend(self, cfg, monkeypatch, capsys):
        monkeypatch.setattr("shesh_omniroute.cli.load_config", lambda: cfg)
        monkeypatch.setattr("shesh_omniroute.cli.detect_backend", lambda: None)
        assert main(["status"]) == 0
        assert "backend: NONE" in capsys.readouterr().out

    def test_start_full_flow(self, cfg, monkeypatch, capsys):
        fb = FakeBackend(rc=0)
        monkeypatch.setattr("shesh_omniroute.cli.load_config", lambda: cfg)
        monkeypatch.setattr("shesh_omniroute.cli.detect_backend", lambda: fb)
        monkeypatch.setattr(FakeBackend, "image_present", lambda self, image: True)
        monkeypatch.setattr("shesh_omniroute.cli.wait_healthy", lambda url, timeout=60.0: True)
        assert main(["start"]) == 0
        assert "up: http://localhost:20128/v1" in capsys.readouterr().out
        assert cfg.api_key() is not None
        assert cfg.read_state()["running"] is True

    def test_start_missing_image(self, cfg, monkeypatch, capsys):
        fb = FakeBackend(rc=0)
        monkeypatch.setattr("shesh_omniroute.cli.load_config", lambda: cfg)
        monkeypatch.setattr("shesh_omniroute.cli.detect_backend", lambda: fb)
        monkeypatch.setattr(FakeBackend, "image_present", lambda self, image: False)
        assert main(["start"]) == 3
        assert "build first" in capsys.readouterr().err


def test_malformed_config_raises_instead_of_silent_defaults(tmp_path):
    """Silent-failure sweep guard: a config.json with invalid JSON must raise
    ConfigError (it used to be swallowed, silently reverting to defaults and
    making user settings vanish)."""
    import pytest

    from shesh_omniroute.config import ConfigError, load_config

    (tmp_path / "config.json").write_text("{not json")
    with pytest.raises(ConfigError):
        load_config(config_dir=tmp_path)


def test_missing_config_file_uses_defaults(tmp_path):
    from shesh_omniroute.config import load_config

    cfg = load_config(config_dir=tmp_path)
    assert isinstance(cfg.port, int)
