"""Toda la suite usa bases temporales, sin cargar credenciales reales."""
import os
import tempfile
from pathlib import Path
import pytest

_temporary = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(_temporary.name) / "orm.sqlite3")
os.environ["ORQENTIVA_DB"] = str(Path(_temporary.name) / "demo.sqlite3")


@pytest.fixture(scope="session", autouse=True)
def close_test_engine():
    yield
    from app.database import engine
    engine.dispose()
    _temporary.cleanup()


@pytest.fixture
def session_factory(tmp_path):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    from seed import seed_database

    engine = create_engine("sqlite:///" + str(tmp_path / "application.sqlite3"))
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys = ON")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    seed_database(factory)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture
def client(session_factory, test_password_hash):
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app
    from app.models import User, AuthSession
    from app.auth import token_digest
    from datetime import datetime, timezone, timedelta
    with session_factory.begin() as session:
        for name in ["alfa", "beta", "admin"]:
            user = User(email=f"{name}@example.com", password_hash=test_password_hash,
                        role="super_admin" if name == "admin" else "business_admin",
                        business_id=None if name == "admin" else name)
            session.add(user)
            session.flush()
            session.add(AuthSession(token_hash=token_digest(f"test-{name}"), user_id=user.id,
                                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
    def override_db():
        with session_factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session")
def test_password_hash():
    from app.auth import password_hasher
    return password_hasher.hash("Only-for-tests-123!")


@pytest.fixture(autouse=True)
def isolated_auth_config(monkeypatch):
    from app.routes.auth import login_limiter
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_ALLOWED_ORIGINS", "http://testserver")
    login_limiter.buckets.clear()
    yield
    login_limiter.buckets.clear()
