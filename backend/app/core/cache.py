import json
import hashlib
import logging
from functools import wraps
from typing import Any, Callable

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            redis_client.ping()
        except redis.ConnectionError:
            logger.warning("Redis unavailable — caching disabled")
            redis_client = None
    return redis_client


def _build_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"fb:{prefix}:{digest}"


def cache_result(expire_seconds: int = 300, prefix: str | None = None):
    def decorator(func: Callable) -> Callable:
        cache_prefix = prefix or func.__name__

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_redis()
            if client is None:
                return await func(*args, **kwargs)

            key = _build_cache_key(cache_prefix, *args, **kwargs)
            try:
                cached: str | None = client.get(key)  # type: ignore[assignment]
                if cached is not None:
                    return json.loads(cached)
            except (redis.RedisError, json.JSONDecodeError):
                pass

            result = await func(*args, **kwargs)

            try:
                client.setex(key, expire_seconds, json.dumps(result, default=str))
            except redis.RedisError:
                logger.debug("Cache write failed for %s", key)

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_redis()
            if client is None:
                return func(*args, **kwargs)

            key = _build_cache_key(cache_prefix, *args, **kwargs)
            try:
                cached: str | None = client.get(key)  # type: ignore[assignment]
                if cached is not None:
                    return json.loads(cached)
            except (redis.RedisError, json.JSONDecodeError):
                pass

            result = func(*args, **kwargs)

            try:
                client.setex(key, expire_seconds, json.dumps(result, default=str))
            except redis.RedisError:
                logger.debug("Cache write failed for %s", key)

            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_prefix(prefix: str) -> int:
    client = get_redis()
    if client is None:
        return 0
    cursor = 0
    deleted = 0
    pattern = f"fb:{prefix}:*"
    while True:
        cursor, keys = client.scan(cursor, match=pattern, count=100)  # type: ignore[assignment]
        if keys:
            deleted += client.delete(*keys)  # type: ignore[assignment]
        if cursor == 0:
            break
    return deleted
