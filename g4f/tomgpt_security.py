"""TomGPT access control helpers: shared password auth and per-IP rate limits."""

from __future__ import annotations

import base64
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple


DEFAULT_CHAT_RATE_LIMIT = "20/60"
DEFAULT_GLOBAL_RATE_LIMIT = "180/60"

CHAT_PATH_MARKERS = (
    "/backend-api/v2/conversation",
    "/v1/chat/completions",
    "/v1/responses",
    "/v1/images/",
    "/backend-api/v2/files/",
)


class RateLimiter:
    """Sliding-window limiter keyed by client identity (usually IP)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    def retry_after(self, key: str, now: Optional[float] = None) -> int:
        now = time.monotonic() if now is None else now
        with self._lock:
            bucket = self._hits.get(key)
            if not bucket:
                return self.window_seconds
            oldest = bucket[0]
        return max(1, int(self.window_seconds - (now - oldest)) + 1)


def parse_rate_limit(spec: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse ``requests/window_seconds`` (e.g. ``20/60``). Empty/off disables."""
    if spec is None:
        return None
    text = str(spec).strip().lower()
    if not text or text in {"off", "none", "0", "disabled", "false"}:
        return None
    if "/" not in text:
        raise ValueError(f"Invalid rate limit '{spec}', expected requests/seconds")
    left, right = text.split("/", 1)
    max_requests = int(left.strip())
    window_seconds = int(right.strip())
    if max_requests < 1 or window_seconds < 1:
        raise ValueError(f"Invalid rate limit '{spec}'")
    return max_requests, window_seconds


def resolve_access_password(
    explicit: Optional[str] = None,
    *,
    tomgpt_password: Optional[str] = None,
    g4f_api_key: Optional[str] = None,
) -> Optional[str]:
    for candidate in (explicit, tomgpt_password, g4f_api_key):
        if candidate:
            return candidate
    return None


def is_loopback_host(host: str) -> bool:
    value = (host or "").strip().lower()
    return value in {"127.0.0.1", "localhost", "::1", "[::1]"}


def client_ip(
    remote_addr: Optional[str],
    x_forwarded_for: Optional[str] = None,
    *,
    trust_proxy: bool = False,
) -> str:
    if trust_proxy and x_forwarded_for:
        first = x_forwarded_for.split(",", 1)[0].strip()
        if first:
            return first
    return (remote_addr or "unknown").strip() or "unknown"


def check_access_secret(
    authorization: Optional[str],
    password: str,
    *,
    api_key_header: Optional[str] = None,
) -> bool:
    """Accept HTTP Basic (any username), Bearer token, or g4f-api-key header."""
    if not password:
        return True
    expected = password.encode("utf-8")

    if api_key_header and secrets.compare_digest(
        api_key_header.encode("utf-8"), expected
    ):
        return True

    if not authorization:
        return False

    scheme, _, remainder = authorization.partition(" ")
    scheme_l = scheme.lower()
    token = remainder.strip()
    if not token:
        return False

    if scheme_l == "bearer":
        return secrets.compare_digest(token.encode("utf-8"), expected)

    if scheme_l == "basic":
        try:
            decoded = base64.b64decode(token).decode("utf-8")
        except Exception:
            return False
        _user, sep, passwd = decoded.partition(":")
        if not sep:
            return False
        return secrets.compare_digest(passwd.encode("utf-8"), expected)

    return False


def is_chat_heavy_path(path: str) -> bool:
    path = path or ""
    return any(marker in path for marker in CHAT_PATH_MARKERS)


def is_static_asset_path(path: str) -> bool:
    path = path or ""
    return path.startswith("/dist/") or path.endswith(
        (".css", ".js", ".map", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg", ".woff2")
    )
