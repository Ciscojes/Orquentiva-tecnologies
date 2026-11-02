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
def client(session_factory):
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app
    def override_db():
        with session_factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
