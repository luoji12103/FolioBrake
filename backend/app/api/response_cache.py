from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import json

_cache = {}

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method != "GET":
            return await call_next(request)
        
        cache_key = hashlib.md5(str(request.url).encode()).hexdigest()
        if cache_key in _cache:
            from starlette.responses import JSONResponse
            return JSONResponse(content=_cache[cache_key])
        
        response = await call_next(request)
        return response
