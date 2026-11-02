"""API educativa multiempresa. Las claves demo no son autenticación de producción."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, Business, Service
from app.routes.leads import router as leads_router

DEMO_KEYS = {"demo-barberia-alfa": "alfa", "demo-barberia-beta": "beta"}
app = FastAPI(title="ORQENTIVA AI", version="0.1.0", description="API educativa multiempresa")
app.include_router(leads_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    if request.url.path == "/leads":
        return JSONResponse(status_code=422, content={"detail": "Datos de contacto inválidos"})
    return await request_validation_exception_handler(request, exc)


def current_business(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key or x_api_key not in DEMO_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key de demostración inválida")
    return DEMO_KEYS[x_api_key]


class AppointmentIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
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
