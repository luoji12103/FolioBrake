from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import asyncio

from app.core.security_logger import log_rate_limit_exceeded


class RateLimiter:
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
        self.requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        async with self._lock:
            if client_ip not in self.requests:
                self.requests[client_ip] = []

            self.requests[client_ip] = [
                t for t in self.requests[client_ip] if current_time - t < self.period
            ]

            if len(self.requests[client_ip]) >= self.calls:
                log_rate_limit_exceeded(
                    client_ip=client_ip,
                    path=request.url.path,
                    limit=self.calls,
                )
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            self.requests[client_ip].append(current_time)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [t for t in self.requests[client_ip] if current_time - t < 60]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            log_rate_limit_exceeded(
                client_ip=client_ip,
                path=request.url.path,
                limit=self.requests_per_minute,
            )
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        self.requests[client_ip].append(current_time)
        response = await call_next(request)
        return response
