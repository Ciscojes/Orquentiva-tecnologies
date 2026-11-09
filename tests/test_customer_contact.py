"""Contacto del cliente en reservas públicas: obligatorio, validado y visible para el negocio."""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.contact import normalize_contact
from app.routes.public_booking import limiter

ALFA = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}


@pytest.mark.parametrize("raw,expected", [
    ("8888-1234", "88881234"),
    ("+506 8888 1234", "+50688881234"),
    ("(506) 2222-3333", "50622223333"),
    ("Ana@Example.COM", "ana@example.com"),
])
def test_normalize_valid_contacts(raw, expected):
    assert normalize_contact(raw) == expected


@pytest.mark.parametrize("raw", ["123", "no tengo", "ana@", "8888-1234 ext", "1" * 16])
def test_reject_invalid_contacts(raw):
    with pytest.raises(ValueError):
        normalize_contact(raw)


@pytest.fixture
def slot(client):
    limiter.buckets.clear()
    service = client.post("/client/services", headers=ALFA, json={"name": "Corte recto", "duration_minutes": 30, "price_crc": 5000}).json()
    days = [{"weekday": i, "is_closed": False, "opens_at": "09:00", "closes_at": "13:00"} for i in range(7)]
    client.put("/client/hours", headers=ALFA, json={"days": days}).raise_for_status()
    client.post("/client/team", headers=ALFA, json={"name": "Ana", "days": days, "service_ids": [service["id"]]}).raise_for_status()
    params = {"day": (date.today() + timedelta(days=7)).isoformat(), "service_id": service["id"]}
    stamp = client.get("/book/alfa/availability", params=params).json()[0]
    return {"customer_name": "Pedro", "service_id": service["id"], "starts_at": stamp, "request_key": str(uuid4())}


def test_public_booking_requires_valid_contact(client, slot):
    assert client.post("/book/alfa", json=slot).status_code == 422
    assert client.post("/book/alfa", json={**slot, "customer_contact": "   "}).status_code == 422
    assert client.post("/book/alfa", json={**slot, "customer_contact": "llámame"}).status_code == 422
    assert not client.get("/client/dashboard", headers=ALFA).json()["appointments"]


def test_contact_is_stored_and_shown_to_the_business(client, slot):
    payload = {**slot, "customer_contact": "Pedro@Correo.com"}
    assert client.post("/book/alfa", json=payload).status_code == 201
    [booking] = client.get("/client/dashboard", headers=ALFA).json()["appointments"]
    assert booking["customer_contact"] == "pedro@correo.com"
    # Un reintento con la misma clave pero otro contacto no se acepta como la misma reserva.
    assert client.post("/book/alfa", json={**payload, "customer_contact": "8888-1234"}).status_code == 409
