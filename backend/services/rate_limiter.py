import asyncio
import time
from collections import defaultdict, deque
from typing import Dict
from fastapi import HTTPException, Request, status

from ..config import settings


class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter per client IP address.
    Thread-safe and requires no external Redis/database dependency.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        # Check standard reverse proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Client IP is the first IP in the X-Forwarded-For chain
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    async def check(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        ip = self._get_client_ip(request)
        now = time.time()
        cutoff = now - self.window_seconds

        async with self._lock:
            # Periodic cleanup of idle IPs every 5 minutes
            if now - self._last_cleanup > 300:
                expired_ips = [
                    k for k, timestamps in self._requests.items()
                    if not timestamps or timestamps[-1] < cutoff
                ]
                for k in expired_ips:
                    del self._requests[k]
                self._last_cleanup = now

            timestamps = self._requests[ip]
            # Evict timestamps outside the sliding window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.requests_per_minute:
                retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "status": "error",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded ({self.requests_per_minute} requests/minute). Please slow down.",
                        "hint": f"Retry your plant scan after {retry_after} second(s).",
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)


# Global rate limiter and inference concurrency semaphore
rate_limiter = InMemoryRateLimiter(requests_per_minute=settings.RATE_LIMIT_RPM)
_inference_semaphore: asyncio.Semaphore = None


def get_inference_semaphore() -> asyncio.Semaphore:
    global _inference_semaphore
    if _inference_semaphore is None:
        _inference_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCES)
    return _inference_semaphore
