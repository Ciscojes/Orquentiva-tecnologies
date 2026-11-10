"""Disponibilidad y confirmación para el negocio autenticado."""
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import ConfigDict, Field
from sqlalchemy import select
from app.deps import Database, Tenant
from app.models import Professional, Service
from app.scheduling import require_agenda
from app.schemas import Confirmation, WeekIn
from app.services.agenda import available, confirm_booking

router = APIRouter(prefix="/client", tags=["agenda"])


class MemberIn(WeekIn):
    name: str = Field(min_length=1, max_length=100)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    service_ids: list[int] = Field(max_length=500)


def member_view(row):
    return {"id": row.id, "name": row.name, "days": row.days, "service_ids": row.service_ids}


def save_member(payload, business_id, session, member_id=None):
    require_agenda(session, business_id, lock=True)
    member = session.get(Professional, member_id) if member_id is not None else Professional(business_id=business_id)
    if not member or member.business_id != business_id:
        raise HTTPException(404, "Profesional no encontrado")
    ids = sorted(set(payload.service_ids))
    owned = session.scalars(select(Service.id).where(Service.business_id == business_id, Service.id.in_(ids))).all()
    if len(ids) != len(owned):
        raise HTTPException(422, "Servicios inválidos")
    member.name = payload.name
    member.service_ids = ids
    member.days = [d.model_dump() for d in sorted(payload.days, key=lambda d: d.weekday)]
    session.add(member)
    session.commit()
    return member_view(member)


@router.post("/team", status_code=201)
def add_member(payload: MemberIn, business_id: Tenant, session: Database):
    return save_member(payload, business_id, session)


@router.put("/team/{member_id}")
def edit_member(member_id: int, payload: MemberIn, business_id: Tenant, session: Database):
    return save_member(payload, business_id, session, member_id)


@router.get("/availability")
def availability(day: date, service_id: int, business_id: Tenant, session: Database, professional_id: int | None = None):
    require_agenda(session, business_id)
    return [{"starts_at": stamp, "professional_ids": ids} for stamp, ids in sorted(available(session, business_id, day, service_id, professional_id).items())]


@router.post("/bookings", status_code=201)
def confirm(payload: Confirmation, business_id: Tenant, session: Database):
    return confirm_booking(payload, business_id, session)
