"""Administración mínima de negocios; nunca autoriza cuentas de cliente."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import UserCreate, create_user, require_super_admin, user_view
from app.database import get_db
from app.models import AuthSession, Business, User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_super_admin)])
Database = Annotated[Session, Depends(get_db)]


class BusinessIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    id: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9][a-z0-9-]*$")
    booking_enabled: StrictBool = True
    name: str = Field(min_length=1, max_length=150)


class BusinessState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: StrictBool


class BusinessUserIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=12, max_length=128)


def business_view(business: Business):
    return {"id": business.id, "name": business.name, "is_active": business.is_active, "booking_enabled": business.booking_enabled}


def find_business(session: Session, business_id: str, *, lock=False):
    query = select(Business).where(Business.id == business_id)
    if lock:
        query = query.with_for_update()
    business = session.scalar(query)
    if business is None:
        raise HTTPException(404, "Empresa no encontrada")
    return business


@router.get("/businesses")
def businesses(session: Database):
    return [business_view(row) for row in session.scalars(select(Business).order_by(Business.name, Business.id))]


@router.post("/businesses", status_code=201)
def add_business(payload: BusinessIn, session: Database):
    business = Business(**payload.model_dump())
    session.add(business)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "El identificador de negocio ya existe") from None
    return business_view(business)


@router.patch("/businesses/{business_id}")
def change_business_state(business_id: str, payload: BusinessState, session: Database):
    business = find_business(session, business_id, lock=True)
    business.is_active = payload.is_active
    if not payload.is_active:
        users = select(User.id).where(User.business_id == business_id)
        session.execute(delete(AuthSession).where(AuthSession.user_id.in_(users)))
    session.commit()
    return business_view(business)


class AgendaState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    booking_enabled: StrictBool


@router.put("/businesses/{business_id}/agenda")
def set_agenda(business_id: str, payload: AgendaState, session: Database):
    business = find_business(session, business_id, lock=True)
    business.booking_enabled = payload.booking_enabled
    session.commit()
    return business_view(business)


@router.get("/businesses/{business_id}/users")
def business_users(business_id: str, session: Database):
    find_business(session, business_id)
    users = session.scalars(select(User).where(User.business_id == business_id).order_by(User.email))
    return [{**user_view(user), "is_active": user.is_active} for user in users]


@router.post("/businesses/{business_id}/users", status_code=201)
def add_business_user(business_id: str, payload: BusinessUserIn, session: Database):
    from pydantic import ValidationError
    find_business(session, business_id)
    try:
        data = UserCreate(email=payload.email, password=payload.password, role="business_admin", business_id=business_id)
    except ValidationError:
        raise HTTPException(422, "Correo o contraseña inválidos") from None
    try:
        user = create_user(session, data)
        session.commit()
    except (ValueError, IntegrityError):
        session.rollback()
        raise HTTPException(409, "La cuenta ya existe; no se modificó") from None
    return {**user_view(user), "is_active": user.is_active}
