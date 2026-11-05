"""API multiempresa con autenticación por sesiones revocables."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import current_business
from app.routes.auth import router as auth_router
from app.database import get_db
from app.models import Appointment, Business, Service
from app.routes.leads import router as leads_router

app = FastAPI(title="ORQENTIVA AI", version="0.1.0", description="API educativa multiempresa")
app.include_router(leads_router)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    if request.url.path == "/leads" or request.url.path.startswith("/auth/"):
        return JSONResponse(status_code=422, content={"detail": "Datos inválidos"})
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Servicio temporalmente no disponible"})


@app.middleware("http")
async def private_cache_policy(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/auth/", "/business/", "/services", "/appointments")):
        response.headers["Cache-Control"] = "no-store"
    return response


class AppointmentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_name: str = Field(min_length=1, max_length=100)
    starts_at: datetime


def utc_iso(value: datetime) -> str:
    # SQLite de pruebas devuelve sin tzinfo las fechas guardadas en UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@app.get("/health")
def health():
    return {"status": "ok", "project": "ORQENTIVA AI", "version": "0.1.0"}


@app.get("/business/me")
def my_business(business_id: Annotated[str, Depends(current_business)], session: Annotated[Session, Depends(get_db)]):
    business = session.get(Business, business_id)
    if business is None:
        raise HTTPException(404, "Empresa no encontrada")
    return {"id": business.id, "name": business.name}


@app.get("/services")
def services(business_id: Annotated[str, Depends(current_business)], session: Annotated[Session, Depends(get_db)]):
    rows = session.scalars(select(Service).where(Service.business_id == business_id).order_by(Service.id))
    return [{"id": row.id, "name": row.name, "price_crc": row.price_crc} for row in rows]


@app.get("/appointments")
def appointments(business_id: Annotated[str, Depends(current_business)], session: Annotated[Session, Depends(get_db)]):
    rows = session.scalars(select(Appointment).where(Appointment.business_id == business_id)
                           .order_by(Appointment.starts_at, Appointment.id))
    return [{"id": row.id, "customer_name": row.customer_name, "starts_at": utc_iso(row.starts_at)} for row in rows]


@app.post("/appointments", status_code=201)
def create_appointment(payload: AppointmentIn, business_id: Annotated[str, Depends(current_business)],
                       session: Annotated[Session, Depends(get_db)]):
    if payload.starts_at.tzinfo is None or payload.starts_at.utcoffset() is None:
        raise HTTPException(422, "Se requiere fecha con zona horaria (por ejemplo -06:00)")
    if session.get(Business, business_id) is None:
        raise HTTPException(404, "Empresa no encontrada")
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
