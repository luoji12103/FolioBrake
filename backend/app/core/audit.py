"""Business-action audit logging.

Complements ``security_logger`` (which handles security events like auth
failures and rate limits) by recording *who did what* on business resources.

All entries include the correlation ID from the current request context so
traces can be followed end-to-end.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from app.core.logging_config import get_correlation_id


class AuditAction(str, Enum):
    USER_REGISTER = "user.register"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_UPDATE = "user.update"
    USER_DEACTIVATE = "user.deactivate"

    APIKEY_CREATE = "api_key.create"
    APIKEY_REVOKE = "api_key.revoke"

    PORTFOLIO_VIEW = "portfolio.view"
    PORTFOLIO_MODIFY = "portfolio.modify"

    TRADE_PLACE = "trade.place"
    TRADE_CANCEL = "trade.cancel"

    REPORT_GENERATE = "report.generate"
    REPORT_EXPORT = "report.export"

    BACKTEST_RUN = "backtest.run"

    CONFIG_CHANGE = "config.change"

    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"


_audit_logger: structlog.BoundLogger | None = None


def _get_audit_logger() -> structlog.BoundLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = structlog.get_logger("audit")
    assert _audit_logger is not None
    return _audit_logger


def log_audit_event(
    action: str | AuditAction,
    *,
    user_id: int | str | None = None,
    username: str | None = None,
    resource: str | None = None,
    resource_id: str | int | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    success: bool = True,
) -> None:
    """Record a business-action audit event.

    Args:
        action: What happened (use ``AuditAction`` enum or free-form string).
        user_id: ID of the user who performed the action.
        username: Username for readability.
        resource: Resource type affected (e.g. ``"portfolio"``, ``"trade"``).
        resource_id: Specific resource instance.
        details: Arbitrary extra context.
        ip_address: Client IP if available.
        success: Whether the action succeeded.
    """
    logger = _get_audit_logger()

    event_value = action.value if isinstance(action, AuditAction) else action

    log_data: dict[str, Any] = {
        "audit_action": event_value,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": get_correlation_id(),
    }

    if user_id is not None:
        log_data["user_id"] = user_id
    if username is not None:
        log_data["username"] = username
    if resource is not None:
        log_data["resource"] = resource
    if resource_id is not None:
        log_data["resource_id"] = resource_id
    if details:
        log_data["details"] = details
    if ip_address is not None:
        log_data["ip_address"] = ip_address

    log_method = logger.info if success else logger.warning
    log_method("audit_event", **log_data)
