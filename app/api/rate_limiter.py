"""
app/api/rate_limiter.py — In-memory sliding-window rate limiter for FastAPI.
Protects LLM and compute-intensive endpoints from denial-of-service and credit exhaustion.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_key: str) -> tuple[bool, int]:
        """
        Check if request is allowed under the sliding window.
        Returns (allowed: bool, retry_after_seconds: int).
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_key]
            # Prune timestamps older than cutoff
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._requests[client_key] = valid_timestamps

            if len(valid_timestamps) >= self.max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                return False, retry_after

            valid_timestamps.append(now)
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware applying rate limiting to compute-intensive endpoints.
    Excludes /health, /ready, /docs, /openapi.json.
    """

    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Only rate-limit chat and feedback API paths
        if path.startswith("/api/v1/chat") or path.startswith("/api/v1/feedback"):
            # Determine client IP (support proxies like Nginx)
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            elif request.client and request.client.host:
                client_ip = request.client.host
            else:
                client_ip = "unknown"

            allowed, retry_after = self.limiter.is_allowed(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded (অনুরোধের সীমা অতিক্রম করেছে)",
                        "message": (
                            f"Too many requests. Please wait {retry_after} seconds "
                            "before submitting your next query."
                        ),
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)

