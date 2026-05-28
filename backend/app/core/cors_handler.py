from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class CORSPreflightHandler(BaseHTTPMiddleware):
    """Handle CORS preflight requests using configured origins.

    In production, uses explicit allowed origins from settings.
    In dev, falls back to a permissive policy (no credentials).
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            from starlette.responses import Response

            configured = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
            origin = request.headers.get("origin", "")

            if configured:
                allow_origin = origin if origin in configured else configured[0]
                allow_credentials = "true"
            else:
                allow_origin = "*"
                allow_credentials = "false"

            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": allow_origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-API-Key, X-Request-ID",
                    "Access-Control-Allow-Credentials": allow_credentials,
                    "Access-Control-Max-Age": "600",
                },
            )
        return await call_next(request)
