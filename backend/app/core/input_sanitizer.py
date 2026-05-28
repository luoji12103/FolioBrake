"""Input sanitization middleware.

Provides defense-in-depth against injection attacks by rejecting requests
that contain suspicious characters in query parameters.  This is NOT a
substitute for proper parameterized queries (SQLAlchemy handles that) –
it is an additional layer that blocks obvious attack payloads before they
reach application code.
"""

from __future__ import annotations

import re
import logging
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Patterns that should never appear in query-string values.
# '<' and '>' catch basic XSS; single/double quotes catch SQL injection
# attempts (legitimate inputs should not contain raw quotes in URLs).
_SUSPICIOUS_RE = re.compile(r'[<>"\';]')

# Maximum number of query parameters allowed (prevent parameter-pollution DoS).
_MAX_QUERY_PARAMS = 50


class InputSanitizerMiddleware(BaseHTTPMiddleware):
    """Block requests with suspicious characters in query parameters."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # --- query-string checks ---
        params = request.query_params
        if len(params) > _MAX_QUERY_PARAMS:
            logger.warning("too_many_query_params", extra={"count": len(params)})
            raise HTTPException(status_code=400, detail="Too many query parameters")

        for key, value in params.items():
            if _SUSPICIOUS_RE.search(value):
                logger.warning(
                    "suspicious_input_blocked",
                    extra={"param": key, "client": request.client.host if request.client else "unknown"},
                )
                raise HTTPException(status_code=400, detail="Invalid characters in input")
            # Also check the key itself
            if _SUSPICIOUS_RE.search(key):
                logger.warning(
                    "suspicious_param_key",
                    extra={"param": key, "client": request.client.host if request.client else "unknown"},
                )
                raise HTTPException(status_code=400, detail="Invalid characters in parameter name")

        # --- path-parameter checks (basic) ---
        for segment in request.url.path.split("/"):
            if segment and _SUSPICIOUS_RE.search(segment):
                logger.warning(
                    "suspicious_path_segment",
                    extra={"segment": segment, "client": request.client.host if request.client else "unknown"},
                )
                raise HTTPException(status_code=400, detail="Invalid characters in URL path")

        return await call_next(request)
