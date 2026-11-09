"""Endpoints históricos de agenda sin profesionales (negocio autenticado)."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models import Appointment, Business, Professional, Service
from app.routes.client import Database, Tenant
from app.scheduling import require_agenda

router = APIRouter(tags=["agenda básica"])


class AppointmentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_name: str = Field(min_length=1, max_length=100)
    starts_at: datetime


def utc_iso(value: datetime) -> str:
    # SQLite de pruebas devuelve sin tzinfo las fechas guardadas en UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@router.get("/business/me")
def my_business(business_id: Tenant, session: Database):
    business = session.get(Business, business_id)
    if business is None:
        raise HTTPException(404, "Empresa no encontrada")
    return {"id": business.id, "name": business.name}


@router.get("/services")
def services(business_id: Tenant, session: Database):
    require_agenda(session, business_id)
    rows = session.scalars(select(Service).where(Service.business_id == business_id).order_by(Service.id))
    return [{"id": row.id, "name": row.name, "price_crc": row.price_crc} for row in rows]


@router.get("/appointments")
def appointments(business_id: Tenant, session: Database):
    require_agenda(session, business_id)
    rows = session.scalars(select(Appointment).where(Appointment.business_id == business_id)
                           .order_by(Appointment.starts_at, Appointment.id))
    return [{"id": row.id, "customer_name": row.customer_name, "starts_at": utc_iso(row.starts_at)} for row in rows]


@router.post("/appointments", status_code=201)
def create_appointment(payload: AppointmentIn, business_id: Tenant, session: Database):
    if payload.starts_at.tzinfo is None or payload.starts_at.utcoffset() is None:
        raise HTTPException(422, "Se requiere fecha con zona horaria (por ejemplo -06:00)")
    require_agenda(session, business_id, lock=True)
    if session.scalar(select(Professional.id).where(Professional.business_id == business_id).limit(1)) is not None:
        raise HTTPException(409, "Confirma el servicio y profesional mediante la agenda")
    appointment = Appointment(business_id=business_id, customer_name=payload.customer_name,
                              starts_at=payload.starts_at.astimezone(timezone.utc))
    session.add(appointment)
    try:
        # La restricción única resuelve también las solicitudes simultáneas.
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Horario ya reservado para esta empresa") from None
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "No se pudo guardar la reserva") from None
    return {"id": appointment.id, "business_id": appointment.business_id,
            "customer_name": appointment.customer_name, "starts_at": utc_iso(appointment.starts_at)}
