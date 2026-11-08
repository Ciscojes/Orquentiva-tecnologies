"""SPEC-007: credenciales, permisos, CSRF y aislamiento con base temporal."""
from datetime import datetime, timedelta, timezone
from typing import Annotated
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.auth import (COOKIE_NAME, token_digest, UserCreate, create_user, require_super_admin, verify_password)
from app.models import User, AuthSession
from app.main import app
from app.database import get_db

ORIGIN = {"Origin": "http://testserver"}
PASSWORD = "Only-for-tests-123!"
def login(client, email="alfa@example.com", password=PASSWORD):
    return client.post("/auth/login", headers=ORIGIN, json={"email": email, "password": password})


def test_login_cookie_hashes_and_logout_revocation(client, session_factory):
    response = login(client, "  ALFA@example.com  ")
    assert response.status_code == 200
    assert response.json()["role"] == "business_admin"
    assert response.headers["cache-control"] == "no-store"
    assert "HttpOnly" in response.headers["set-cookie"] and "SameSite=strict" in response.headers["set-cookie"]
    token = client.cookies[COOKIE_NAME]
    assert len(token) >= 43 and token not in response.text and PASSWORD not in response.text
    with session_factory() as session:
        row = session.get(AuthSession, token_digest(token))
        user = session.get(User, row.user_id)
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash
        assert row.token_hash != token
    assert client.get("/business/me").json()["id"] == "alfa"
    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204
    assert client.get("/auth/me", headers={"Cookie": f"{COOKIE_NAME}={token}"}).status_code == 401
    assert client.post("/auth/logout", headers=ORIGIN).status_code == 204


def test_cookie_secure_by_default(client, monkeypatch):
    monkeypatch.delenv("AUTH_COOKIE_SECURE", raising=False)
    assert "Secure" in login(client).headers["set-cookie"]


def test_invalid_credentials_are_generic(client, session_factory):
    a = login(client, password="wrong-password")
    b = login(client, email="missing@example.com")
    with session_factory.begin() as session:
        session.scalar(select(User).where(User.email == "alfa@example.com")).is_active = False
    c = login(client)
    assert a.status_code == b.status_code == c.status_code == 401
    assert a.json() == b.json() == c.json()
    assert COOKIE_NAME not in client.cookies


@pytest.mark.parametrize("path", ["/auth/me", "/business/me", "/services", "/appointments"])
def test_demo_keys_no_longer_authorize(client, path):
    assert client.get(path, headers={"X-API-Key": "demo-barberia-alfa"}).status_code == 401
    assert client.get(path, headers={"Cookie": f"{COOKIE_NAME}=forged"}).status_code == 401


def test_expired_and_disabled_sessions(client, session_factory):
    login(client)
    token = client.cookies[COOKIE_NAME]
    with session_factory.begin() as session:
        session.get(AuthSession, token_digest(token)).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert client.get("/auth/me").status_code == 401
    login(client)
    with session_factory.begin() as session:
        session.scalar(select(User).where(User.email == "alfa@example.com")).is_active = False
    assert client.get("/services").status_code == 401


def test_login_rotates_session(client):
    login(client)
    previous = client.cookies[COOKIE_NAME]
    login(client)
    assert client.cookies[COOKIE_NAME] != previous
    assert client.get("/auth/me", headers={"Cookie": f"{COOKIE_NAME}={previous}"}).status_code == 401


def test_origin_protection_and_no_spoofed_host(client):
    payload = {"email": "alfa@example.com", "password": PASSWORD}
    for headers in [{}, {"Origin": "https://evil.example"}, {"Origin": "null"}, {"Origin": "http://testserver.evil.example", "Host": "testserver.evil.example"}]:
        assert client.post("/auth/login", json=payload, headers=headers).status_code == 403
    login(client)
    assert client.post("/auth/logout").status_code == 403
    assert client.get("/auth/me").status_code == 200
    appointment = {"customer_name": "QA", "starts_at": "2035-01-01T12:00:00Z"}
    assert client.post("/appointments", json=appointment).status_code == 403
    assert client.post("/appointments", json=appointment, headers=ORIGIN).status_code == 201


def test_roles_and_tenant_tampering(client):
    login(client)
    assert client.get("/business/me?business_id=beta").json()["id"] == "alfa"
    assert client.get("/services?business_id=beta", headers={"X-API-Key": "demo-barberia-beta"}).json()[0]["name"] == "Corte clásico"
    assert client.post("/appointments", headers=ORIGIN, json={"business_id": "beta", "customer_name": "QA", "starts_at": "2035-01-01T12:00:00Z"}).status_code == 422
    login(client, "admin@example.com")
    assert client.get("/auth/me").json()["business_id"] is None
    assert client.get("/appointments").status_code == 403
    # Verificar la dependencia administrativa sin añadir rutas de prueba a la app real.
    from fastapi import FastAPI
    restricted = FastAPI()
    restricted.dependency_overrides[get_db] = app.dependency_overrides[get_db]
    @restricted.get("/admin-test")
    def admin_endpoint(user: Annotated[User, Depends(require_super_admin)]):
        return {"ok": True}
    with TestClient(restricted) as other:
        assert other.get("/admin-test", headers={"Cookie": f"{COOKIE_NAME}=test-alfa"}).status_code == 403
        assert other.get("/admin-test", headers={"Cookie": f"{COOKIE_NAME}=test-admin"}).status_code == 200


def test_login_rate_limit_and_validation_privacy(client):
    invalid = client.post("/auth/login", headers=ORIGIN, json={"email": "invalid", "password": "SECRET-SHOULD-NOT-REFLECT"})
    assert invalid.status_code == 422 and "SECRET" not in invalid.text
    for _ in range(5):
        assert login(client, password="wrong-password").status_code == 401
    response = login(client)
    assert response.status_code == 429 and response.headers["retry-after"] == "60"


def test_create_user_validation_and_no_overwrite(client, session_factory):
    from pydantic import ValidationError
    for role, business in [("super_admin", "alfa"), ("business_admin", None)]:
        with pytest.raises(ValidationError):
            UserCreate(email="new@example.com", password=PASSWORD, role=role, business_id=business)
    payload = UserCreate(email=" New@example.com ", password=PASSWORD, role="business_admin", business_id="beta")
    with session_factory.begin() as session:
        user = create_user(session, payload)
        assert user.email == "new@example.com" and verify_password(PASSWORD, user.password_hash)
    with session_factory.begin() as session:
        with pytest.raises(ValueError, match="ya existe"):
            create_user(session, payload)
    with session_factory.begin() as session:
        with pytest.raises(ValueError, match="no existe"):
            create_user(session, payload.model_copy(update={"email": "other@example.com", "business_id": "missing"}))
    with pytest.raises(IntegrityError), session_factory.begin() as session:
        session.add(User(email="bad@example.com", password_hash="unused", role="super_admin", business_id="alfa"))


def test_database_errors_are_private(client):
    from unittest.mock import Mock
    db = Mock()
    db.scalar.side_effect = SQLAlchemyError("secret connection details")
    def broken_db():
        yield db
    app.dependency_overrides[get_db] = broken_db
    response = login(client)
    assert response.status_code == 503 and "secret" not in response.text
