"""Captación pública de solicitudes comerciales."""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.services.rate_limit import RateLimiter

router = APIRouter()


class LeadIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=254)
    company: str | None = Field(default=None, max_length=150)
    service: Literal["agents", "automation", "growth", "saas"]
    message: str = Field(min_length=10, max_length=2000)


limiter = RateLimiter()


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
