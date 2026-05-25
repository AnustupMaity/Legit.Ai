import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

import config


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP rate limiter (free, no Redis)."""

    def __init__(self, app, requests_per_minute: int):
        super().__init__(app)
        self.limit = max(1, requests_per_minute)
        self.window = 60.0
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _allow(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            times = [t for t in self._hits[ip] if now - t < self.window]
            if len(times) >= self.limit:
                self._hits[ip] = times
                return False
            times.append(now)
            self._hits[ip] = times
            return True

    async def dispatch(self, request: Request, call_next):
        if not config.RATE_LIMIT_ENABLED:
            return await call_next(request)
        if request.url.path in ("/", "/health", "/docs", "/openapi.json", "/redoc", "/ml_pipeline/jobs", "/api/ml_pipeline/jobs"):
            return await call_next(request)
        ip = self._client_ip(request)
        if not self._allow(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a minute."},
            )
        return await call_next(request)
