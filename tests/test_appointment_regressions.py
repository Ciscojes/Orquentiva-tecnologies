"""Regresiones de reservas con bases exclusivas para cada prueba."""
from concurrent.futures import ThreadPoolExecutor

from datetime import datetime, timezone
import pytest
from app.models import Appointment

ALFA = {"X-API-Key": "demo-barberia-alfa"}
BETA = {"X-API-Key": "demo-barberia-beta"}


def book(client, stamp, name="Cliente Demo", headers=None):
    return client.post("/appointments", headers=headers or ALFA,
                       json={"customer_name": name, "starts_at": stamp})


@pytest.mark.parametrize("name", ["", " ", "\t\n", "a" * 101])
def test_invalid_customer_name(client, name):
    assert book(client, "2031-01-01T12:00:00-06:00", name).status_code == 422
    assert client.get("/appointments", headers=ALFA).json() == []


def test_trim_name_and_normalize_time(client):
    response = book(client, "2031-01-01T12:00:00-06:00", "  Ana Demo  ")
    assert response.status_code == 201
    assert response.json()["customer_name"] == "Ana Demo"
    assert response.json()["starts_at"] == "2031-01-01T18:00:00+00:00"


def test_equivalent_offsets_and_tenant_isolation(client):
    assert book(client, "2031-01-01T12:00:00-06:00").status_code == 201
    assert book(client, "2031-01-01T18:00:00Z").status_code == 409
    assert book(client, "2031-01-01T18:00:00Z", headers=BETA).status_code == 201


def test_persisted_dates_are_checked_without_rewriting(client, session_factory):
    stamp = "2031-01-01T12:00:00-06:00"
    with session_factory.begin() as session:
        session.add(Appointment(business_id="alfa", customer_name="Reserva anterior",
                                starts_at=datetime.fromisoformat(stamp).astimezone(timezone.utc)))
    assert book(client, "2031-01-01T18:00:00+00:00").status_code == 409
    rows = client.get("/appointments", headers=ALFA).json()
    assert len(rows) == 1
    assert rows[0]["starts_at"] == "2031-01-01T18:00:00+00:00"


def test_concurrent_equivalent_bookings(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda stamp: book(client, stamp).status_code,
                        ["2031-01-01T12:00:00-06:00", "2031-01-01T18:00:00Z"]))
    assert sorted(responses) == [201, 409]


def test_distinct_microseconds_are_not_rounded(client):
    for stamp in ["2031-01-01T18:00:00.000001Z", "2031-01-01T18:00:00.000002Z"]:
        assert book(client, stamp).status_code == 201


def test_listing_orders_persisted_and_new_dates_chronologically(client, session_factory):
    with session_factory.begin() as session:
        session.add(Appointment(business_id="alfa", customer_name="Más tarde",
                                starts_at=datetime(2031, 1, 1, 18, tzinfo=timezone.utc)))
    assert book(client, "2031-01-01T17:00:00Z", "Más temprano").status_code == 201
    assert [row["customer_name"] for row in client.get("/appointments", headers=ALFA).json()] == ["Más temprano", "Más tarde"]
