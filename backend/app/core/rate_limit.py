"""In-memory + Redis-backed sliding-window rate limiter.

Falls back to in-memory tracking when Redis is unavailable.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.cache import get_redis
from app.core.metrics import RATE_LIMIT_HITS

_RL_PREFIX = "fb:rl"


class RateLimiter:
    """Sliding-window rate limiter keyed by client IP."""

    def __init__(self, calls: int = 100, period: int = 60) -> None:
        self.calls = calls
        self.period = period
        self._local: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        current = time.time()

        client = get_redis()
        if client is not None:
            self._check_redis(client, client_ip, current)
        else:
            self._check_memory(client_ip, current)

    def _check_redis(self, client, client_ip: str, current: float) -> None:
        key = f"{_RL_PREFIX}:{client_ip}"
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, current - self.period)
        pipe.zadd(key, {str(current): current})
        pipe.zcard(key)
        pipe.expire(key, self.period)
        results = pipe.execute()
        count = results[2]
        if count > self.calls:
            RATE_LIMIT_HITS.inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.calls} requests per {self.period}s",
            )

    def _check_memory(self, client_ip: str, current: float) -> None:
        timestamps = self._local[client_ip]
        self._local[client_ip] = [t for t in timestamps if current - t < self.period]
        if len(self._local[client_ip]) >= self.calls:
            RATE_LIMIT_HITS.inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.calls} requests per {self.period}s",
            )
        self._local[client_ip].append(current)


standard_rate_limit = RateLimiter(calls=100, period=60)
