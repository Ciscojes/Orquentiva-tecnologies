"""Agenda: catálogo público, turnos libres y confirmación de reservas."""
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.models import Appointment, Business, BusinessHours, Professional, Service
from app.scheduling import LOCAL, require_agenda, utc


def to_clock(value):
    return None if value is None else f"{value // 60:02d}:{value % 60:02d}"


def to_minutes(value):
    return None if value is None else int(value[:2]) * 60 + int(value[3:])


def public_business(session, business_id, lock=False):
    query = select(Business).where(Business.id == business_id, Business.is_active, Business.booking_enabled)
    business = session.scalar(query.with_for_update() if lock else query)
    if business is None:
        raise HTTPException(404, "Agenda no disponible")
    return business


def public_catalog(session, business_id):
    """Servicios reservables y profesionales que los ofrecen."""
    business = public_business(session, business_id)
    members = session.scalars(select(Professional).where(Professional.business_id == business_id)).all()
    eligible = {sid for p in members for sid in p.service_ids}
    services = session.scalars(select(Service).where(Service.business_id == business_id, Service.is_active,
                               Service.duration_minutes.is_not(None), Service.id.in_(eligible))).all()
    return {"name": business.name, "services": [{"id": s.id, "name": s.name, "duration_minutes": s.duration_minutes} for s in services],
            "team": [{"id": p.id, "name": p.name, "service_ids": p.service_ids} for p in members if p.service_ids]}


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


def confirm_booking(payload, business_id, session, commit=True):
    require_agenda(session, business_id, lock=True)
    key = str(payload.request_key)
    existing = session.scalar(select(Appointment).where(Appointment.business_id == business_id, Appointment.request_key == key))
    stamp = utc(payload.starts_at)
    if existing:
        if (existing.customer_name != payload.customer_name or existing.service_id != payload.service_id
                or utc(existing.starts_at) != stamp or payload.professional_id not in (None, existing.professional_id)
                or payload.customer_contact != existing.customer_contact):
            raise HTTPException(409, "Confirmación distinta")
        return {"id": existing.id, "professional_id": existing.professional_id}
    choices = available(session, business_id, stamp.astimezone(LOCAL).date(), payload.service_id, payload.professional_id)
    if stamp not in choices:
        raise HTTPException(409, "Turno no disponible")
    member_id = choices[stamp][0]
    service = session.get(Service, payload.service_id)
    booking = Appointment(business_id=business_id, starts_at=stamp, ends_at=stamp+timedelta(minutes=service.duration_minutes),
                          customer_name=payload.customer_name, professional_id=member_id, service_id=service.id, request_key=key,
                          customer_contact=payload.customer_contact)
    session.add(booking)
    session.flush()
    if commit:
        session.commit()
    return {"id": booking.id, "professional_id": member_id}
