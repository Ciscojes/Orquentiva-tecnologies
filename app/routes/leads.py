"""Captación pública de solicitudes comerciales."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead

router = APIRouter()


class LeadIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=254)
    company: str | None = Field(default=None, max_length=150)
    service: Literal["agents", "automation", "growth", "saas"]
    message: str = Field(min_length=10, max_length=2000)


class LeadLimiter:
    """Límite local por IP: 5 envíos/minuto; memoria acotada.

    Para varias instancias debe sustituirse por un contador compartido.
    No confiar en X-Forwarded-For enviado directamente por el visitante.
    """

    def __init__(self, per_minute: int = 5):
        self.per_minute = per_minute
        self.buckets = OrderedDict()
        self.lock = Lock()

    def allow(self, request: Request) -> bool:
        try:
            self.check(request)
        except HTTPException:
            return False
        return True

    def check(self, request: Request):
        key = request.client.host if request.client else "unknown"
        now = monotonic()
        with self.lock:
            while self.buckets:
                first = next(iter(self.buckets))
                if self.buckets[first][0] + 60 > now:
                    break
                self.buckets.popitem(last=False)
            start, count = self.buckets.get(key, (now, 0))
            if count >= self.per_minute:
                raise HTTPException(429, "Demasiadas solicitudes", headers={"Retry-After": "60"})
            if key not in self.buckets and len(self.buckets) >= 10000:
                raise HTTPException(429, "Inténtalo más tarde", headers={"Retry-After": "60"})
            self.buckets[key] = (start, count + 1)


limiter = LeadLimiter()


@router.post("/leads", status_code=201)
def create_lead(
    payload: LeadIn,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
):
    limiter.check(request)
    lead = Lead(**payload.model_dump())
    session.add(lead)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "No se pudo guardar la solicitud") from None
    return {"status": "created"}
