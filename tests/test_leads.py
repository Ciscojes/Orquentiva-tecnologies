
"""
Pruebas del módulo de captación de leads.

Usamos una base SQLite temporal y aislada para
probar el endpoint sin modificar PostgreSQL real.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Lead
from app.routes.leads import limiter


@pytest.fixture
def client(tmp_path):
    limiter.buckets.clear()
    # Base temporal exclusiva para esta prueba
    database_path = tmp_path / "test_leads.sqlite3"

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    # Crear únicamente la tabla necesaria
    Lead.__table__.create(bind=engine)

    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        with TestingSession() as session:
            yield session

    # Sustituimos PostgreSQL por la base temporal
    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session = TestingSession

    try:
        # Sin context manager: no ejecuta el lifespan
        # que inicializa SQLite de demostración.
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_valid_lead(client):
    """AC-05: una solicitud válida devuelve 201."""

    payload = {
        "name": "Carlos Rodríguez",
        "email": "carlos@example.com",
        "company": "Barbería Premium",
        "service": "agents",
        "message": "Quiero automatizar mis reservas.",
    }

    response = client.post("/leads", json=payload)

    assert response.status_code == 201
    assert response.json() == {"status": "created"}
    with app.state.testing_session() as session:
        lead = session.query(Lead).one()
        assert lead.name == payload["name"]
        assert lead.email == payload["email"]
        assert lead.created_at is not None


def test_reject_invalid_lead(client):
    """AC-07: los datos incorrectos devuelven 422."""

    payload = {
        "name": "",
        "email": "correo-invalido",
        "company": "Barbería Premium",
        "service": "agents",
        "message": "Hola",
    }

    response = client.post("/leads", json=payload)

    assert response.status_code == 422


def test_leads_are_not_publicly_listed(client):
    """AC-11: no existe un listado público de leads."""

    response = client.get("/leads")

    assert response.status_code in (404, 405)


VALID = {"name": "Ana Demo", "email": "ana@example.com", "service": "agents", "message": "Quiero información de reservas."}


@pytest.mark.parametrize("field,value", [
    ("name", "  "), ("name", "a" * 101), ("email", "incorrecto"),
    ("company", "c" * 151), ("service", "unknown"),
    ("message", "         "), ("message", "m" * 2001),
])
def test_validation_boundaries(client, field, value):
    response = client.post("/leads", json={**VALID, field: value})
    assert response.status_code == 422
    assert "ana@example.com" not in response.text
    with app.state.testing_session() as session:
        assert session.query(Lead).count() == 0


def test_rate_limit_and_no_forwarded_ip_bypass(client):
    for _ in range(5):
        assert client.post("/leads", json=VALID).status_code == 201
    response = client.post("/leads", json=VALID, headers={"X-Forwarded-For": "other"})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    with app.state.testing_session() as session:
        assert session.query(Lead).count() == 5


def test_trimmed_values_and_optional_company(client):
    assert client.post("/leads", json={**VALID, "name": "  Ana Demo  "}).status_code == 201
    with app.state.testing_session() as session:
        lead = session.query(Lead).one()
        assert lead.name == "Ana Demo"
        assert lead.company is None


def test_database_failure_is_private(client):
    from sqlalchemy.exc import SQLAlchemyError
    from unittest.mock import Mock
    session = Mock()
    session.commit.side_effect = SQLAlchemyError("private database error")
    def failed_db():
        yield session
    app.dependency_overrides[get_db] = failed_db
    response = client.post("/leads", json=VALID)
    assert response.status_code == 503
    assert "private" not in response.text
    session.rollback.assert_called_once()
