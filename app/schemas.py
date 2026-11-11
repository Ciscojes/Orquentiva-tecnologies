"""Esquemas de entrada que usan varias rutas y servicios."""
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from app.contact import normalize_contact


class DayIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weekday: int = Field(ge=0, le=6, strict=True)
    is_closed: StrictBool
    opens_at: str | None = Field(default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
    closes_at: str | None = Field(default=None, pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")

    @model_validator(mode="after")
    def valid_interval(self):
        if self.is_closed:
            if self.opens_at is not None or self.closes_at is not None:
                raise ValueError("Un día cerrado no tiene intervalo")
        elif self.opens_at is None or self.closes_at is None or self.opens_at >= self.closes_at:
            raise ValueError("Apertura y cierre deben definir un intervalo del mismo día")
        return self


class WeekIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: list[DayIn] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def complete_week(self):
        if {day.weekday for day in self.days} != set(range(7)):
            raise ValueError("Cada día debe aparecer una sola vez")
        return self


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    customer_name: str = Field(min_length=1, max_length=100)
    service_id: int
    professional_id: int | None = None
    starts_at: AwareDatetime
    request_key: UUID
    customer_contact: str | None = Field(default=None, max_length=254)

    @field_validator("customer_contact")
    @classmethod
    def valid_contact(cls, value):
        return None if value is None or not value.strip() else normalize_contact(value)
