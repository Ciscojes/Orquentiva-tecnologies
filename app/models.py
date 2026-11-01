

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[str] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    price_crc: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class Appointment(Base):
    __tablename__ = "appointments"

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "starts_at",
            name="uq_appointment_business_time",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[str] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
