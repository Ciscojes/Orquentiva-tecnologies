
from datetime import datetime

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
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

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (CheckConstraint("duration_minutes IS NULL OR (duration_minutes >= 5 AND duration_minutes <= 480)", name="ck_service_duration"),)

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

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)


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



class Lead(Base):
    """
    Solicitud comercial recibida desde la página
    corporativa de ORQENTIVA Technologies.
    """

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )

    company: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'super_admin' AND business_id IS NULL) OR "
            "(role = 'business_admin' AND business_id IS NOT NULL)",
            name="ck_user_role_business",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


class BusinessHours(Base):
    __tablename__ = "business_hours"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_hours_weekday"),
        CheckConstraint("(is_closed AND opens_at IS NULL AND closes_at IS NULL) OR "
                        "(NOT is_closed AND opens_at IS NOT NULL AND closes_at IS NOT NULL "
                        "AND opens_at >= 0 AND closes_at <= 1439 AND opens_at < closes_at)", name="ck_hours_interval"),
    )
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    opens_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    closes_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
