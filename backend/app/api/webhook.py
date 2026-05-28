import ipaddress
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(tags=["webhook"])

_BLOCKED_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal", "[::1]"})


def _reject_private_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname in _BLOCKED_HOSTS:
        raise ValueError(f"Webhook URL must not target {hostname}")
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError("Webhook URL must not target a private or reserved IP")
    except ValueError:
        pass


class WebhookConfig(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)
    events: list[str] = Field(..., min_length=1, max_length=50)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        _reject_private_url(v)
        return v


@router.post("/register")
def register_webhook(config: WebhookConfig):
    return {"status": "registered", "url": config.url, "events": config.events}


@router.get("/test")
def test_webhook(url: str):
    if len(url) < 10 or len(url) > 2000:
        raise HTTPException(status_code=400, detail="Invalid URL length")
    try:
        _reject_private_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "message": f"Would send to {url}"}
