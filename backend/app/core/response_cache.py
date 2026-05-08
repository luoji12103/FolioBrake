import json
import hashlib
import logging

import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.core.cache import get_redis

logger = logging.getLogger(__name__)

CACHEABLE_PATHS = (
    "/api/risk/state",
    "/api/risk/state-history",
    "/api/risk/overlay",
    "/api/risk/correlation",
    "/api/risk/var",
    "/api/reports/",
)

DEFAULT_TTL = 120


async def _read_body(response: StreamingResponse) -> bytes:
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:  # type: ignore[union-attr]
        if isinstance(chunk, (bytes, bytearray)):
            chunks.append(bytes(chunk))
        elif isinstance(chunk, str):
            chunks.append(chunk.encode())
        else:
            chunks.append(bytes(chunk))
    return b"".join(chunks)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.method != "GET":
            return await call_next(request)

        path = request.url.path
        if not any(path.startswith(p) for p in CACHEABLE_PATHS):
            return await call_next(request)

        client = get_redis()
        if client is None:
            return await call_next(request)

        key = f"fb:resp:{hashlib.sha256(str(request.url).encode()).hexdigest()[:16]}"
        try:
            cached: str | None = client.get(key)  # type: ignore[assignment]
            if cached is not None:
                data = json.loads(cached)
                return Response(
                    content=data["body"].encode() if isinstance(data["body"], str) else data["body"],
                    status_code=data["status"],
                    media_type="application/json",
                )
        except (redis.RedisError, json.JSONDecodeError, KeyError):
            pass

        response = await call_next(request)

        if 200 <= response.status_code < 300 and isinstance(response, StreamingResponse):
            body = await _read_body(response)

            try:
                client.setex(
                    key,
                    DEFAULT_TTL,
                    json.dumps({"body": body.decode(), "status": response.status_code}),
                )
            except redis.RedisError:
                pass

            return Response(
                content=body,
                status_code=response.status_code,
                media_type=response.media_type,
            )

        return response
