from datetime import datetime, timezone
from contextlib import closing
import hashlib
import sqlite3

import pytest
from sqlalchemy import select

from app.models import Appointment
from scripts.import_legacy_sqlite import transfer


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript("""
            CREATE TABLE businesses (id TEXT, name TEXT);
            CREATE TABLE services (business_id TEXT, name TEXT, price_crc INTEGER);
            CREATE TABLE appointments (business_id TEXT, customer_name TEXT, starts_at TEXT);
            INSERT INTO businesses VALUES ('alfa', 'Barbería Alfa');
            INSERT INTO services VALUES ('alfa', 'Corte clásico', 5000);
            INSERT INTO appointments VALUES ('alfa', 'QA Histórico', '2034-01-01T12:00:00-06:00');
        """)
    return path


def test_dry_run_leaves_source_and_target_untouched(source, session_factory):
    before = hashlib.sha256(source.read_bytes()).digest()
    assert transfer(source, session_factory) == {"mode": "dry-run", "businesses": 0, "services": 0, "appointments": 1}
    assert hashlib.sha256(source.read_bytes()).digest() == before
    with session_factory() as session:
        assert session.scalars(select(Appointment)).all() == []


def test_apply_normalizes_dates_and_is_repeatable(source, session_factory):
    assert transfer(source, session_factory, apply=True)["appointments"] == 1
    assert transfer(source, session_factory, apply=True)["appointments"] == 0
    with session_factory() as session:
        row = session.scalars(select(Appointment)).one()
        assert row.customer_name == "QA Histórico"
        assert row.starts_at.replace(tzinfo=timezone.utc) == datetime(2034, 1, 1, 18, tzinfo=timezone.utc)


def test_conflicting_booking_is_not_overwritten(source, session_factory):
    with session_factory.begin() as session:
        session.add(Appointment(business_id="alfa", customer_name="Otra reserva", starts_at=datetime(2034, 1, 1, 18, tzinfo=timezone.utc)))
    with pytest.raises(ValueError, match="horario"):
        transfer(source, session_factory, apply=True)
    with session_factory() as session:
        assert session.scalars(select(Appointment)).one().customer_name == "Otra reserva"


@pytest.mark.parametrize("stamp", ["2034-01-01T18:00:00", "2034-01-01T18:00:00Z"])
def test_invalid_or_duplicate_source_is_rejected(source, session_factory, stamp):
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute("INSERT INTO appointments VALUES ('alfa', 'QA', ?)", (stamp,))
    with pytest.raises(ValueError):
        transfer(source, session_factory, apply=True)
    with session_factory() as session:
        assert session.scalars(select(Appointment)).all() == []


def test_missing_source_is_not_created(tmp_path, session_factory):
    path = tmp_path / "missing.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        transfer(path, session_factory)
    assert not path.exists()


def test_duplicate_services_are_rejected(source, session_factory):
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute("INSERT INTO services VALUES ('alfa', 'Corte clásico', 5000)")
    with pytest.raises(ValueError, match="servicios"):
        transfer(source, session_factory, apply=True)


def test_new_business_service_and_booking_are_inserted_together(source, session_factory):
    from app.models import Business, Service
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute("INSERT INTO businesses VALUES ('gamma', 'Empresa QA')")
        connection.execute("INSERT INTO services VALUES ('gamma', 'Servicio QA', 6000)")
        connection.execute("INSERT INTO appointments VALUES ('gamma', 'QA', '2034-01-01T18:00:00Z')")
    result = transfer(source, session_factory, apply=True)
    assert (result["businesses"], result["services"], result["appointments"]) == (1, 1, 2)
    with session_factory() as session:
        assert session.get(Business, "gamma") is not None
        assert session.scalar(select(Service).where(Service.business_id == "gamma")).price_crc == 6000
        assert len(session.scalars(select(Appointment)).all()) == 2
