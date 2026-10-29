import os
from pathlib import Path
import tempfile

# Configure DB before importing application.
_temp = tempfile.TemporaryDirectory()
os.environ["ORQENTIVA_DB"] = str(Path(_temp.name) / "test.sqlite3")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app, init_db  # noqa: E402

init_db()
client = TestClient(app)
ALFA = {"X-API-Key": "demo-barberia-alfa"}
BETA = {"X-API-Key": "demo-barberia-beta"}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_requires_key():
    assert client.get("/services").status_code == 401


def test_each_business_sees_own_services():
    assert client.get("/services", headers=ALFA).json()[0]["name"] == "Corte clásico"
    assert client.get("/services", headers=BETA).json()[0]["name"] == "Corte premium"


def test_book_and_isolate_tenants():
    payload = {"customer_name": "Cliente Demo", "starts_at": "2030-11-02T15:00:00-06:00"}
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 201
    assert len(client.get("/appointments", headers=ALFA).json()) == 1
    assert client.get("/appointments", headers=BETA).json() == []
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 409
    assert client.post("/appointments", headers=BETA, json=payload).status_code == 201


def test_requires_timezone():
    payload = {"customer_name": "Cliente Demo", "starts_at": "2030-11-02T15:00:00"}
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 422
