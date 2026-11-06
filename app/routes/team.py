"""Disponibilidad y confirmación para el negocio autenticado."""
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import select
from app.models import Appointment, BusinessHours, Professional, Service
from app.routes.client import Database, Tenant, WeekIn, to_minutes
from app.scheduling import LOCAL, require_agenda, utc

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


def available(session, business_id, day, service_id, professional_id):
    service = session.get(Service, service_id)
    if not service or service.business_id != business_id or not service.is_active or not service.duration_minutes:
        raise HTTPException(422, "Servicio no disponible")
    hours = session.get(BusinessHours, (business_id, day.weekday()))
    if not hours or hours.is_closed:
        return {}
    if day < datetime.now(LOCAL).date() or (day - datetime.now(LOCAL).date()).days > 365:
        return {}
    midnight = datetime.combine(day, time(), LOCAL).astimezone(timezone.utc)
    members = select(Professional).where(Professional.business_id == business_id).order_by(Professional.id)
    if professional_id is not None:
        members = members.where(Professional.id == professional_id)
    bookings = session.scalars(select(Appointment).where(Appointment.business_id == business_id,
        Appointment.starts_at < midnight + timedelta(days=1),
        (Appointment.ends_at > midnight) | ((Appointment.ends_at.is_(None)) & (Appointment.starts_at >= midnight)))).all()
    if any(b.ends_at is None for b in bookings):
        return {}
    result = {}
    now = datetime.now(timezone.utc)
    for member in session.scalars(members):
        shift = member.days[day.weekday()]
        if service_id not in member.service_ids or shift["is_closed"]:
            continue
        start = max(hours.opens_at, to_minutes(shift["opens_at"]))
        stop = min(hours.closes_at, to_minutes(shift["closes_at"]))
        for minute in range(start, stop - service.duration_minutes + 1, 5):
            stamp = (midnight + timedelta(minutes=minute)).astimezone(timezone.utc)
            end = stamp + timedelta(minutes=service.duration_minutes)
            if stamp <= now or any(b.professional_id == member.id and utc(b.starts_at) < end and stamp < utc(b.ends_at) for b in bookings):
                continue
            result.setdefault(stamp, []).append(member.id)
    return result


@router.get("/availability")
def availability(day: date, service_id: int, business_id: Tenant, session: Database, professional_id: int | None = None):
    require_agenda(session, business_id)
    return [{"starts_at": stamp, "professional_ids": ids} for stamp, ids in sorted(available(session, business_id, day, service_id, professional_id).items())]


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    customer_name: str = Field(min_length=1, max_length=100)
    service_id: int
    professional_id: int | None = None
    starts_at: AwareDatetime
    request_key: UUID


@router.post("/bookings", status_code=201)
def confirm(payload: Confirmation, business_id: Tenant, session: Database):
    require_agenda(session, business_id, lock=True)
    key = str(payload.request_key)
    existing = session.scalar(select(Appointment).where(Appointment.business_id == business_id, Appointment.request_key == key))
    stamp = utc(payload.starts_at)
    if existing:
        if (existing.customer_name != payload.customer_name or existing.service_id != payload.service_id
                or utc(existing.starts_at) != stamp or payload.professional_id not in (None, existing.professional_id)):
            raise HTTPException(409, "Confirmación distinta")
        return {"id": existing.id, "professional_id": existing.professional_id}
    choices = available(session, business_id, stamp.astimezone(LOCAL).date(), payload.service_id, payload.professional_id)
    if stamp not in choices:
        raise HTTPException(409, "Turno no disponible")
    member_id = choices[stamp][0]
    service = session.get(Service, payload.service_id)
    booking = Appointment(business_id=business_id, starts_at=stamp, ends_at=stamp+timedelta(minutes=service.duration_minutes),
                          customer_name=payload.customer_name, professional_id=member_id, service_id=service.id, request_key=key)
    session.add(booking)
    session.commit()
    return {"id": booking.id, "professional_id": member_id}
