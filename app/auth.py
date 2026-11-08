"""Autenticación por sesión opaca; no admite las antiguas claves demo."""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthSession, Business, User

COOKIE_NAME = "orqentiva_session"
SESSION_SECONDS = 8 * 60 * 60
password_hasher = PasswordHash.recommended()
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def secure_cookie() -> bool:
    return os.getenv("AUTH_COOKIE_SECURE", "true").lower() != "false"


def verify_origin(request: Request):
    allowed = {value.strip() for value in os.getenv("AUTH_ALLOWED_ORIGINS", "").split(",") if value.strip()}
    if request.headers.get("origin") not in allowed:
        raise HTTPException(403, "Origen no autorizado")


def verify_password(password: str, stored_hash: str | None) -> bool:
    try:
        return password_hasher.verify(password, stored_hash or _dummy_hash)
    except (ValueError, TypeError):
        return False


def new_session(session: Session, user: User) -> str:
    now = datetime.now(timezone.utc)
    # Limpiar sesiones caducadas de esta cuenta; no afecta sesiones de otros usuarios.
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id, AuthSession.expires_at <= now))
    token = secrets.token_urlsafe(32)
    session.add(AuthSession(token_hash=token_digest(token), user_id=user.id,
                            expires_at=now + timedelta(seconds=SESSION_SECONDS)))
    return token


def current_user(request: Request, session: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(COOKIE_NAME, "")
    if not token or len(token) > 128:
        raise HTTPException(401, "Se requiere una sesión válida")
    row = session.get(AuthSession, token_digest(token))
    if row is None:
        raise HTTPException(401, "Se requiere una sesión válida")
    expires = row.expires_at
    if expires.tzinfo is None:  # SQLite de pruebas.
        expires = expires.replace(tzinfo=timezone.utc)
    user = session.get(User, row.user_id)
    if expires <= datetime.now(timezone.utc) or user is None or not user.is_active:
        raise HTTPException(401, "Se requiere una sesión válida")
    if user.role == "business_admin":
        business = session.get(Business, user.business_id)
        if business is None or not business.is_active:
            raise HTTPException(403, "Empresa no disponible")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        verify_origin(request)
    return user


def current_business(user: Annotated[User, Depends(current_user)],
                     session: Annotated[Session, Depends(get_db)]) -> str:
    if user.role != "business_admin" or not user.business_id:
        raise HTTPException(403, "Se requiere una cuenta de negocio")
    if session.get(Business, user.business_id) is None:
        raise HTTPException(403, "Empresa no disponible")
    return user.business_id


def require_super_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "super_admin":
        raise HTTPException(403, "Se requiere administración de plataforma")
    return user


def user_view(user: User):
    return {"id": user.id, "email": user.email, "role": user.role, "business_id": user.business_id}


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["super_admin", "business_admin"]
    business_id: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def role_business(self):
        if (self.role == "business_admin") != (self.business_id is not None):
            raise ValueError("La empresa es obligatoria solo para administradores de negocio")
        if not self.password.strip():
            raise ValueError("Contraseña inválida")
        return self


def create_user(session: Session, payload: UserCreate) -> User:
    if session.scalar(select(User.id).where(User.email == str(payload.email))) is not None:
        raise ValueError("La cuenta ya existe; no se sobrescribió")
    if payload.business_id and session.get(Business, payload.business_id) is None:
        raise ValueError("La empresa indicada no existe")
    user = User(email=str(payload.email), password_hash=password_hasher.hash(payload.password),
                role=payload.role, business_id=payload.business_id)
    session.add(user)
    session.flush()
    return user
