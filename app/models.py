
from datetime import datetime, timezone

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy import (
    Boolean, JSON, Index, text,
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


class WhatsAppConversation(Base):
    __tablename__ = "whatsapp_conversations"
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), primary_key=True)
    sender: Mapped[str] = mapped_column(String(128), primary_key=True)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String(256), unique=True)
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"))
    phone_id: Mapped[str] = mapped_column(String(128))
    sender: Mapped[str] = mapped_column(String(128))
    body: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reply: Mapped[str | None] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)


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


    booking_enabled: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True)


class Professional(Base):
    __tablename__ = "professionals"
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id"))
    name: Mapped[str] = mapped_column(String(100))
    service_ids: Mapped[list] = mapped_column(JSON)
    days: Mapped[list] = mapped_column(JSON)


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
        UniqueConstraint("professional_id", "starts_at", name="uq_prof_time"),
        UniqueConstraint("business_id", "request_key", name="uq_booking_request"),
        Index("uq_legacy_time", "business_id", "starts_at", unique=True,
              postgresql_where=text("professional_id IS NULL"), sqlite_where=text("professional_id IS NULL")),
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



    professional_id: Mapped[int | None] = mapped_column(ForeignKey("professionals.id", name="fk_booking_prof"))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id", name="fk_booking_service"))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    request_key: Mapped[str | None] = mapped_column(String(36))
    # Teléfono o correo para avisar al cliente; obligatorio en las reservas públicas.
    customer_contact: Mapped[str | None] = mapped_column(String(254))


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
        # La aplicación fija la fecha: la base de demo SQLite creada por migraciones no tiene now().
        default=lambda: datetime.now(timezone.utc),
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
