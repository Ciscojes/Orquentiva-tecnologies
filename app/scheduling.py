"""Shared serialization point for schedule changes and confirmations."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models import Business

LOCAL = timezone(timedelta(hours=-6))


def require_agenda(session, business_id, *, lock=False):
    if lock and session.get_bind().dialect.name == "sqlite":
        session.execute(update(Business).where(Business.id == business_id).values(booking_enabled=Business.booking_enabled))
    query = select(Business).where(Business.id == business_id)
    business = session.scalar(query.with_for_update() if lock else query)
    if not business or not business.booking_enabled:
        raise HTTPException(409, "Agenda no habilitada")
    return business


def utc(value: datetime):
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
