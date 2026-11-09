"""Servicios y horario del negocio autenticado; reservas de solo lectura."""
from datetime import timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.auth import current_business
from app.database import get_db
from app.models import Appointment, Business, BusinessHours, Service

from app.scheduling import require_agenda, utc
from app.models import Professional

router = APIRouter(prefix="/client", tags=["client"])
Tenant = Annotated[str, Depends(current_business)]
Database = Annotated[Session, Depends(get_db)]
TIME_ZONE = "America/Costa_Rica"


class ServiceIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=150)
    price_crc: int = Field(ge=0, le=10000000, strict=True)
    duration_minutes: int = Field(ge=5, le=480, strict=True)
    is_active: StrictBool = True


class DayIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weekday: int = Field(ge=0, le=6, strict=True)
    is_closed: StrictBool
    opens_at: str | None = Field(default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
    closes_at: str | None = Field(default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")

    @model_validator(mode="after")
    def valid_interval(self):
        if self.is_closed:
            if self.opens_at is not None or self.closes_at is not None:
                raise ValueError("Un día cerrado no tiene intervalo")
        elif self.opens_at is None or self.closes_at is None or self.opens_at >= self.closes_at:
            raise ValueError("Apertura y cierre deben definir un intervalo del mismo día")
        return self


class WeekIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: list[DayIn] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def complete_week(self):
        if {day.weekday for day in self.days} != set(range(7)):
            raise ValueError("Cada día debe aparecer una sola vez")
        return self


def service_view(row: Service):
    return {"id": row.id, "name": row.name, "price_crc": row.price_crc,
            "duration_minutes": row.duration_minutes, "is_active": row.is_active}


def to_clock(value):
    return None if value is None else f"{value // 60:02d}:{value % 60:02d}"


def to_minutes(value):
    return None if value is None else int(value[:2]) * 60 + int(value[3:])


def hours_view(rows):
    by_day = {row.weekday: row for row in rows}
    return {"configured": len(by_day) == 7, "days": [
        {"weekday": day, "is_closed": by_day[day].is_closed if day in by_day else True,
         "opens_at": to_clock(by_day[day].opens_at) if day in by_day else None,
         "closes_at": to_clock(by_day[day].closes_at) if day in by_day else None}
        for day in range(7)]}


@router.get("/dashboard")
def dashboard(business_id: Tenant, session: Database):
    business = session.get(Business, business_id)
    if not business.booking_enabled:
        return {"booking_enabled": False, "business": {"id": business.id, "name": business.name, "time_zone": TIME_ZONE}}
    team = session.scalars(select(Professional).where(Professional.business_id == business_id).order_by(Professional.id)).all()
    services = session.scalars(select(Service).where(Service.business_id == business_id).order_by(Service.id))
    appointments = session.scalars(select(Appointment).where(Appointment.business_id == business_id)
                                   .order_by(Appointment.starts_at, Appointment.id))
    bookings = []
    for row in appointments:
        stamp = row.starts_at if row.starts_at.tzinfo else row.starts_at.replace(tzinfo=timezone.utc)
        bookings.append({"id": row.id, "customer_name": row.customer_name, "customer_contact": row.customer_contact,
                         "starts_at": stamp.astimezone(timezone.utc).isoformat()})
        if row.professional_id is not None:
            bookings[-1].update(professional_id=row.professional_id, service_id=row.service_id, ends_at=utc(row.ends_at).isoformat())
    hours = session.scalars(select(BusinessHours).where(BusinessHours.business_id == business_id)).all()
    return {"booking_enabled": True, "team": [{"id": p.id, "name": p.name, "service_ids": p.service_ids, "days": p.days} for p in team], "business": {"id": business.id, "name": business.name, "time_zone": TIME_ZONE},
            "services": [service_view(row) for row in services], "appointments": bookings, "hours": hours_view(hours)}


@router.post("/services", status_code=201)
def add_service(payload: ServiceIn, business_id: Tenant, session: Database):
    require_agenda(session, business_id, lock=True)
    service = Service(business_id=business_id, **payload.model_dump())
    session.add(service)
    session.commit()
    return service_view(service)


@router.put("/services/{service_id}")
def edit_service(service_id: int, payload: ServiceIn, business_id: Tenant, session: Database):
    require_agenda(session, business_id, lock=True)
    service = session.scalar(select(Service).where(Service.id == service_id, Service.business_id == business_id))
    if service is None:
        raise HTTPException(404, "Servicio no encontrado")
    for key, value in payload.model_dump().items():
        setattr(service, key, value)
    session.commit()
    return service_view(service)


@router.put("/hours")
def save_hours(payload: WeekIn, business_id: Tenant, session: Database):
    require_agenda(session, business_id, lock=True)
    session.execute(delete(BusinessHours).where(BusinessHours.business_id == business_id))
    rows = [BusinessHours(business_id=business_id, weekday=day.weekday, is_closed=day.is_closed,
                          opens_at=to_minutes(day.opens_at), closes_at=to_minutes(day.closes_at)) for day in payload.days]
    session.add_all(rows)
    session.commit()
    return hours_view(rows)
