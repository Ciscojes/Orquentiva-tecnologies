"""Public booking link: exposes bookable catalog and free slots only."""
from datetime import date
from fastapi import APIRouter, HTTPException, Request
from app.deps import Database
from app.schemas import Confirmation
from app.services.agenda import available, confirm_booking, public_business, public_catalog
from app.services.rate_limit import RateLimiter

router = APIRouter(prefix="/book/{business_id}", tags=["reservas"])
limiter = RateLimiter()


@router.get("")
def catalog(business_id: str, session: Database):
    return public_catalog(session, business_id)


@router.get("/availability")
def slots(business_id: str, session: Database, day: date, service_id: int, professional_id: int | None = None):
    public_business(session, business_id)
    return sorted(available(session, business_id, day, service_id, professional_id))


@router.post("", status_code=201)
def reserve(business_id: str, payload: Confirmation, request: Request, session: Database):
    limiter.check(request)
    if not payload.customer_contact:
        raise HTTPException(422, "Indica un teléfono o correo de contacto")
    public_business(session, business_id, lock=True)
    return confirm_booking(payload, business_id, session)
