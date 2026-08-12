"""Health-wait for the gateway — stdlib HTTP with bounded retries."""

from __future__ import annotations

import time
import urllib.error
import urllib.request


def probe(base_url: str, timeout: float = 3.0) -> bool:
    """True when the OpenAI-compatible endpoint answers (any HTTP status)."""
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except urllib.error.HTTPError as e:
        # 401/403 = server IS up, just needs the key. HTTPError wraps an open
        # response object — it must be closed or its socket leaks.
        e.close()
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_healthy(base_url: str, timeout: float = 60.0, interval: float = 1.0, sleep=time.sleep, now=time.monotonic) -> bool:
    deadline = now() + timeout
    while now() < deadline:
        if probe(base_url):
            return True
        sleep(interval)
    return False
