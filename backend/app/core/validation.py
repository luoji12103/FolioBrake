from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body:
                        import json
                        json.loads(body)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid JSON body")
        response = await call_next(request)
        return response
