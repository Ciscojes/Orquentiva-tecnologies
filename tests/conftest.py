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
