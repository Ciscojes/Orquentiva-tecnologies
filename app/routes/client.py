"""Servicios y horario del negocio autenticado; reservas de solo lectura."""
from datetime import timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import select, delete

from app.deps import Database, Tenant
from app.models import Appointment, Business, BusinessHours, Professional, Service
from app.scheduling import require_agenda, utc
from app.schemas import WeekIn
from app.services.agenda import to_clock, to_minutes

router = APIRouter(prefix="/client", tags=["client"])
TIME_ZONE = "America/Costa_Rica"


class ServiceIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=150)
    price_crc: int = Field(ge=0, le=10000000, strict=True)
    duration_minutes: int = Field(ge=5, le=480, strict=True)
    is_active: StrictBool = True


def service_view(row: Service):
    return {"id": row.id, "name": row.name, "price_crc": row.price_crc,
            "duration_minutes": row.duration_minutes, "is_active": row.is_active}


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
