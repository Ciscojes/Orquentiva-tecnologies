"""Inicio, consulta y cierre de sesiones."""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.auth import (COOKIE_NAME, SESSION_SECONDS, current_user, new_session,
                      secure_cookie, token_digest, user_view, verify_origin, verify_password)
from app.database import get_db
from app.models import AuthSession, Business, User
from app.routes.leads import LeadLimiter

router = APIRouter(prefix="/auth", tags=["auth"])
login_limiter = LeadLimiter()  # Instancia independiente: 5 intentos/IP/minuto.


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


@router.post("/login", dependencies=[Depends(verify_origin)])
def login(payload: LoginIn, request: Request, response: Response,
          session: Annotated[Session, Depends(get_db)]):
    login_limiter.check(request)
    user = session.scalar(select(User).where(User.email == str(payload.email)))
    valid = verify_password(payload.password, user.password_hash if user else None)
    if not valid or user is None or not user.is_active:
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if user.role == "business_admin":
        business = session.scalar(select(Business).where(Business.id == user.business_id).with_for_update())
        if business is None or not business.is_active:
            raise HTTPException(401, "Correo o contraseña incorrectos")
    previous = request.cookies.get(COOKIE_NAME)
    if previous:
        session.execute(delete(AuthSession).where(AuthSession.token_hash == token_digest(previous)))
    token = new_session(session, user)
    session.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=secure_cookie(), samesite="strict", path="/")
    return user_view(user)


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]):
    return user_view(user)


@router.post("/logout", status_code=204, dependencies=[Depends(verify_origin)])
def logout(request: Request, session: Annotated[Session, Depends(get_db)]):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        session.execute(delete(AuthSession).where(AuthSession.token_hash == token_digest(token)))
        session.commit()
    response = Response(status_code=204)
    response.delete_cookie(COOKIE_NAME, path="/", secure=secure_cookie(), httponly=True, samesite="strict")
    return response
