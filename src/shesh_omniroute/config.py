"""Config for the OmniRoute gateway wrapper — paths, image, port, API key."""

from __future__ import annotations

import dataclasses
import json
import os
import secrets as _secrets
from pathlib import Path

DEFAULT_PORT = 20128
DEFAULT_IMAGE = "localhost/shesh-omniroute:latest"
DEFAULT_FORK = "https://github.com/gaganjainse/OmniRoute.git"
DEFAULT_REF = "release/v3.8.50"
CONTAINER_NAME = "shesh-omniroute"

CONFIG_DIR = Path(os.environ.get("SHESH_CONFIG_HOME", Path.home() / ".config" / "shesh" / "omniroute"))


@dataclasses.dataclass
class Config:
    port: int = DEFAULT_PORT
    image: str = DEFAULT_IMAGE
    fork_repo: str = DEFAULT_FORK
    fork_ref: str = DEFAULT_REF
    container_name: str = CONTAINER_NAME
    config_dir: Path = dataclasses.field(default=CONFIG_DIR)

    @property
    def base_url(self) -> str:
        return f"http://localhost:{self.port}/v1"

    @property
    def api_key_path(self) -> Path:
        return self.config_dir / "api.key"

    @property
    def state_path(self) -> Path:
        return self.config_dir / "state.json"

    def api_key(self) -> str | None:
        try:
            key = self.api_key_path.read_text().strip()
        except OSError:
            return None
        return key or None

    def ensure_api_key(self) -> str:
        """Load or create the gateway key; always 0600, never logged.

        The generated key lives only in the config dir's api.key file. To
        source it from an external store instead, pre-seed api.key from
        your secret manager (e.g. gopass/KeePassXC via shesh-secrets refs).
        """
        existing = self.api_key()
        if existing:
            return existing
        key = "sk-shesh-" + _secrets.token_urlsafe(32)
        self._write_key(key)
        return key

    def _write_key(self, key: str) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.api_key_path.write_text(key + "\n")
        os.chmod(self.api_key_path, 0o600)

    def write_state(self, **fields: object) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "container": self.container_name,
            "image": self.image,
            "base_url": self.base_url,
            **fields,
        }
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")

    def read_state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}


def load_config(config_dir: Path | None = None) -> Config:
    """Env wins over file wins over defaults."""
    cfg = Config()
    if config_dir is not None:
        cfg.config_dir = config_dir
    file_settings: dict = {}
    try:
        file_settings = json.loads((cfg.config_dir / "config.json").read_text())
    except (OSError, json.JSONDecodeError):
        pass
    cfg.port = int(os.environ.get("SHESH_OMNIROUTE_PORT", file_settings.get("port", cfg.port)))
    cfg.image = os.environ.get("SHESH_OMNIROUTE_IMAGE", file_settings.get("image", cfg.image))
    return cfg
