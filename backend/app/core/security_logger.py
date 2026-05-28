"""Security event logging.

Provides structured security event logging that integrates with the
existing structlog configuration. All security events are logged with
a ``security`` event type for easy filtering and alerting.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from app.core.logging_config import get_correlation_id


class SecurityEvent(str, Enum):
    """Common security event types."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_MISSING_KEY = "auth_missing_key"
    AUTH_INVALID_KEY = "auth_invalid_key"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_REQUEST = "invalid_request"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCESS_DENIED = "access_denied"
    CSP_VIOLATION = "csp_violation"
    INPUT_VALIDATION_FAILURE = "input_validation_failure"


_security_logger: structlog.BoundLogger | None = None


def _get_security_logger() -> structlog.BoundLogger:
    """Get or create the security logger singleton."""
    global _security_logger
    if _security_logger is None:
        _security_logger = structlog.get_logger("security")
    assert _security_logger is not None
    return _security_logger


def log_security_event(
    event_type: str | SecurityEvent,
    details: dict[str, Any] | None = None,
    severity: str = "WARNING",
    *,
    client_ip: str | None = None,
    path: str | None = None,
    method: str | None = None,
) -> None:
    """Log a security event with structured context.

    Args:
        event_type: The type of security event (use SecurityEvent enum or string).
        details: Additional context about the event.
        severity: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        client_ip: Client IP address if available.
        path: Request path if available.
        method: HTTP method if available.
    """
    logger = _get_security_logger()

    event_value = event_type.value if isinstance(event_type, SecurityEvent) else event_type

    log_data: dict[str, Any] = {
        "security_event": event_value,
        "severity": severity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": get_correlation_id(),
    }

    if details:
        log_data["details"] = details
    if client_ip:
        log_data["client_ip"] = client_ip
    if path:
        log_data["path"] = path
    if method:
        log_data["method"] = method

    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method("security_event", **log_data)


def log_auth_success(api_key: str, client_ip: str | None = None) -> None:
    """Log successful authentication."""
    log_security_event(
        SecurityEvent.AUTH_SUCCESS,
        details={"api_key_prefix": api_key[:4] + "***" if len(api_key) > 4 else "***"},
        severity="INFO",
        client_ip=client_ip,
    )


def log_auth_failure(reason: str, client_ip: str | None = None) -> None:
    """Log failed authentication attempt."""
    event_type = (
        SecurityEvent.AUTH_MISSING_KEY
        if reason == "missing"
        else SecurityEvent.AUTH_INVALID_KEY
    )
    log_security_event(
        event_type,
        details={"reason": reason},
        severity="WARNING",
        client_ip=client_ip,
    )


def log_rate_limit_exceeded(
    client_ip: str,
    path: str | None = None,
    limit: int | None = None,
) -> None:
    """Log rate limit exceeded event."""
    details: dict[str, Any] = {"client_ip": client_ip}
    if limit:
        details["rate_limit"] = limit
    log_security_event(
        SecurityEvent.RATE_LIMIT_EXCEEDED,
        details=details,
        severity="WARNING",
        client_ip=client_ip,
        path=path,
    )


def log_suspicious_activity(
    description: str,
    client_ip: str | None = None,
    path: str | None = None,
    **extra: Any,
) -> None:
    """Log suspicious activity."""
    details: dict[str, Any] = {"description": description, **extra}
    log_security_event(
        SecurityEvent.SUSPICIOUS_ACTIVITY,
        details=details,
        severity="ERROR",
        client_ip=client_ip,
        path=path,
    )
