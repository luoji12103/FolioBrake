"""Role-based access control (RBAC).

Roles are hierarchical: viewer < analyst < trader < admin.
Each role inherits all permissions of the roles below it.

Usage as a FastAPI dependency::

    from app.core.rbac import require_role, Role

    @router.get("/admin-only")
    def admin_endpoint(user = Depends(require_role(Role.ADMIN))):
        ...
"""
from __future__ import annotations

from enum import IntEnum
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.security_logger import log_security_event, SecurityEvent


class Role(IntEnum):
    VIEWER = 0
    ANALYST = 1
    TRADER = 2
    ADMIN = 3


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.VIEWER: {"read_data", "view_reports", "view_portfolio"},
    Role.ANALYST: {"read_data", "view_reports", "view_portfolio", "run_analysis", "run_backtest"},
    Role.TRADER: {
        "read_data", "view_reports", "view_portfolio",
        "run_analysis", "run_backtest", "place_paper_trades", "manage_alerts",
    },
    Role.ADMIN: {
        "read_data", "view_reports", "view_portfolio",
        "run_analysis", "run_backtest", "place_paper_trades", "manage_alerts",
        "manage_users", "manage_api_keys", "view_audit_logs", "manage_settings",
    },
}


def get_user_role(user: Any) -> Role:
    if getattr(user, "is_admin", False):
        return Role.ADMIN
    return Role.VIEWER


def has_permission(user: Any, permission: str) -> bool:
    role = get_user_role(user)
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_role(user: Any, minimum_role: Role) -> bool:
    return get_user_role(user) >= minimum_role


def require_role(minimum_role: Role):
    def dependency(current_user: Any = Depends(_get_current_user_dependency)):
        if not has_role(current_user, minimum_role):
            log_security_event(
                SecurityEvent.ACCESS_DENIED,
                details={
                    "required_role": minimum_role.name,
                    "user_role": get_user_role(current_user).name,
                    "user_id": getattr(current_user, "id", None),
                },
                severity="WARNING",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {minimum_role.name} or higher",
            )
        return current_user
    return Depends(dependency)


def require_permission(permission: str):
    def dependency(current_user: Any = Depends(_get_current_user_dependency)):
        if not has_permission(current_user, permission):
            log_security_event(
                SecurityEvent.ACCESS_DENIED,
                details={
                    "required_permission": permission,
                    "user_role": get_user_role(current_user).name,
                    "user_id": getattr(current_user, "id", None),
                },
                severity="WARNING",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return current_user
    return Depends(dependency)


def _get_current_user_dependency():
    from app.api.auth import get_current_user
    return get_current_user
