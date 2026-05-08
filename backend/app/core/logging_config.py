"""Structured logging with correlation-ID propagation.

Every log line is JSON with at minimum:
  - timestamp (ISO 8601)
  - level
  - event / message
  - correlation_id  (auto-injected via middleware or manual bind)
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(cid: str | None = None) -> str:
    cid = cid or uuid.uuid4().hex[:12]
    _correlation_id.set(cid)
    return cid


# ── structlog processors ───────────────────────────────────────────────────


def _add_correlation_id(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def setup_logging(*, json_format: bool = True, level: str = "INFO") -> None:
    """Configure structlog + stdlib logging once at startup."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(logging.StreamHandler())
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


# ── Correlation-ID middleware ──────────────────────────────────────────────


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Extract or generate a correlation ID for every request and bind it to structlog."""

    _HEADER = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: object) -> Response:
        cid = request.headers.get(self._HEADER) or set_correlation_id()
        set_correlation_id(cid)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=cid,
            method=request.method,
            path=request.url.path,
        )

        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers[self._HEADER] = cid
        return response


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
