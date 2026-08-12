"""shesh-omniroute — Shesh wrapper for the OmniRoute LLM gateway."""

from .backend import Backend, detect_backend
from .config import Config, load_config
from .health import wait_healthy

__all__ = [
    "Backend",
    "Config",
    "detect_backend",
    "load_config",
    "wait_healthy",
]
__version__ = "0.1.0"
