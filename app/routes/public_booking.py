"""Public booking link: exposes bookable catalog and free slots only."""
from datetime import date
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from app.models import Business, Professional, Service
from app.routes.client import Database
from app.routes.leads import LeadLimiter
from app.routes.team import Confirmation, available, confirm

router = APIRouter(prefix="/book/{business_id}", tags=["reservas"])
limiter = LeadLimiter()


def public_business(session, business_id, lock=False):
    query = select(Business).where(Business.id == business_id, Business.is_active, Business.booking_enabled)
    business = session.scalar(query.with_for_update() if lock else query)
    if business is None:
        raise HTTPException(404, "Agenda no disponible")
    return business


@router.get("")
def catalog(business_id: str, session: Database):
    business = public_business(session, business_id)
    members = session.scalars(select(Professional).where(Professional.business_id == business_id)).all()
    eligible = {sid for p in members for sid in p.service_ids}
    services = session.scalars(select(Service).where(Service.business_id == business_id, Service.is_active,
                               Service.duration_minutes.is_not(None), Service.id.in_(eligible))).all()
    return {"name": business.name, "services": [{"id": s.id, "name": s.name, "duration_minutes": s.duration_minutes} for s in services],
            "team": [{"id": p.id, "name": p.name, "service_ids": p.service_ids} for p in members if p.service_ids]}


@router.get("/availability")
def slots(business_id: str, session: Database, day: date, service_id: int, professional_id: int | None = None):
    public_business(session, business_id)
    return sorted(available(session, business_id, day, service_id, professional_id))


@router.post("", status_code=201)
def reserve(business_id: str, payload: Confirmation, request: Request, session: Database):
    limiter.check(request)
    public_business(session, business_id, lock=True)
    return confirm(payload, business_id, session)
