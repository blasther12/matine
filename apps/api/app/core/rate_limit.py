import asyncio
import hashlib
import secrets
from collections import deque
from dataclasses import dataclass, field
from time import monotonic

from fastapi import HTTPException, Request, status


@dataclass
class _Window:
    requests: deque[float] = field(default_factory=deque)


class InMemoryRateLimiter:
    """Per-process limiter with ephemeral, salted client identifiers."""

    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._salt = secrets.token_bytes(32)
        self._windows: dict[str, _Window] = {}
        self._lock = asyncio.Lock()

    def _key(self, client_host: str) -> str:
        digest = hashlib.blake2s(key=self._salt, digest_size=16)
        digest.update(client_host.encode("utf-8", errors="ignore"))
        return digest.hexdigest()

    async def allow(self, client_host: str) -> tuple[bool, int]:
        now = monotonic()
        cutoff = now - self.window_seconds
        key = self._key(client_host)

        async with self._lock:
            window = self._windows.setdefault(key, _Window())
            while window.requests and window.requests[0] <= cutoff:
                window.requests.popleft()

            if len(window.requests) >= self.limit:
                retry_after = max(1, int(window.requests[0] + self.window_seconds - now) + 1)
                return False, retry_after

            window.requests.append(now)

            # Opportunistic bounded cleanup keeps identifiers for at most one window.
            if len(self._windows) > 2_048:
                stale = [
                    bucket_key
                    for bucket_key, bucket in list(self._windows.items())[:256]
                    if not bucket.requests or bucket.requests[-1] <= cutoff
                ]
                for bucket_key in stale:
                    self._windows.pop(bucket_key, None)

        return True, 0


async def enforce_catalog_rate_limit(request: Request) -> None:
    limiter: InMemoryRateLimiter = request.app.state.catalog_rate_limiter
    client_host = request.client.host if request.client else "unknown"
    allowed, retry_after = await limiter.allow(client_host)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
        )
