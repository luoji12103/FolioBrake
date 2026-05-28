from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import get_db
from app.auth.models import User, APIKey
from app.auth.security import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    generate_api_key,
    hash_api_key,
)

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class CreateAPIKeyRequest(BaseModel):
    name: str | None = Field(None, max_length=128)


def get_current_user(
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = verify_token(token)
        if payload:
            user = db.execute(
                select(User).where(User.id == payload["sub"])
            ).scalar_one_or_none()
            if user and user.is_active:
                return user

    if x_api_key:
        key_hash = hash_api_key(x_api_key)
        api_key = db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
        ).scalar_one_or_none()
        if api_key:
            user = db.execute(
                select(User).where(User.id == api_key.user_id)
            ).scalar_one_or_none()
            if user and user.is_active:
                api_key.last_used = datetime.utcnow()
                return user

    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        select(User).where((User.username == req.username) | (User.email == req.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        display_name=req.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.username)
    return {
        "user_id": user.id,
        "username": user.username,
        "token": token,
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == req.username)
    ).scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_token(user.id, user.username)
    return {
        "user_id": user.id,
        "username": user.username,
        "token": token,
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
        "created_at": str(current_user.created_at),
    }


@router.post("/api-keys")
def create_api_key(
    req: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_key, key_hash = generate_api_key()
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        name=req.name,
    )
    db.add(api_key)
    db.commit()

    return {
        "api_key_id": api_key.id,
        "key": raw_key,
        "name": req.name,
        "warning": "Store this key securely. It cannot be retrieved again.",
    }


@router.get("/api-keys")
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keys = list(
        db.execute(
            select(APIKey).where(APIKey.user_id == current_user.id)
        ).scalars().all()
    )
    return [
        {
            "id": k.id,
            "name": k.name,
            "is_active": k.is_active,
            "created_at": str(k.created_at),
            "last_used": str(k.last_used) if k.last_used else None,
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    key = db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    ).scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    db.commit()
    return {"status": "revoked", "key_id": key_id}


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    users = list(db.execute(select(User).order_by(User.id)).scalars().all())
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": str(u.created_at),
        }
        for u in users
    ]
