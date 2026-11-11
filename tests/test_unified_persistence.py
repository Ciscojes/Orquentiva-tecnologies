from datetime import datetime, timezone
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.main import app
from app.models import Appointment, Business, Service, User, AuthSession
from app.auth import current_business

ALFA = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}


def test_services_come_from_injected_database(client, session_factory):
    with session_factory.begin() as session:
        session.add(Service(business_id="alfa", name="Servicio de prueba ORM", price_crc=1234))
    assert any(row["name"] == "Servicio de prueba ORM" for row in client.get("/services", headers=ALFA).json())


def test_booking_is_persisted_in_injected_database(client, session_factory):
    response = client.post("/appointments", headers=ALFA, json={"customer_name": "QA", "starts_at": "2032-01-01T12:00:00-06:00"})
    assert response.status_code == 201
    with session_factory() as session:
        row = session.scalars(select(Appointment)).one()
        assert row.customer_name == "QA"
        assert row.starts_at.replace(tzinfo=timezone.utc) == datetime(2032, 1, 1, 18, tzinfo=timezone.utc)


def test_business_isolated_and_missing(client, session_factory):
    assert client.get("/business/me", headers=ALFA).json()["id"] == "alfa"
    with session_factory.begin() as session:
        for row in session.scalars(select(Service).where(Service.business_id == "alfa")):
            session.delete(row)
        user = session.scalar(select(User).where(User.business_id == "alfa"))
        for token in session.scalars(select(AuthSession).where(AuthSession.user_id == user.id)):
            session.delete(token)
        session.delete(user)
        session.flush()
        session.delete(session.get(Business, "alfa"))
    assert client.get("/business/me", headers=ALFA).status_code == 401
    assert client.post("/appointments", headers=ALFA, json={"customer_name": "QA", "starts_at": "2032-01-01T18:00:00Z"}).status_code == 401


def test_startup_does_not_touch_legacy_sqlite(tmp_path, monkeypatch):
    path = tmp_path / "legacy.sqlite3"
    monkeypatch.setenv("ORQENTIVA_DB", str(path))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
    assert not path.exists()


def test_booking_database_failure_is_private(client):
    session = Mock()
    session.scalar.side_effect = [Mock(booking_enabled=True), None]  # negocio con agenda clásica, sin profesionales
    session.commit.side_effect = SQLAlchemyError("private SQL details")
    def failed_db():
        yield session
    app.dependency_overrides[get_db] = failed_db
    app.dependency_overrides[current_business] = lambda: "alfa"
    response = client.post("/appointments", headers=ALFA, json={"customer_name": "QA", "starts_at": "2032-01-01T18:00:00Z"})
    assert response.status_code == 503
    assert "private" not in response.text
    session.rollback.assert_called_once()
    app.dependency_overrides.pop(current_business, None)


def test_missing_database_configuration_fails_on_connect_not_on_import():
    import pytest
    from app.database import MISSING, make_engine
    engine = make_engine(None, None)  # Crear el motor no conecta ni lanza errores.
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        engine.connect()
    assert "POSTGRES_PASSWORD" in MISSING
    assert make_engine("sqlite://", None).dialect.name == "sqlite"
    local = make_engine(None, "solo-pruebas").url
    assert (local.host, local.port, local.database) == ("127.0.0.1", 5434, "orqentiva_db")
