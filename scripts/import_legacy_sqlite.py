"""Traslado explícito de SQLite a la base configurada. Por defecto solo simula.

La fuente se abre en modo lectura. No se imprimen nombres, correos ni fechas.
--apply inserta en una transacción; no borra ni sobrescribe registros existentes.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

from sqlalchemy import select, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.models import Appointment, Business, Service


def transfer(source, session_factory, apply=False):
    with closing(sqlite3.connect(Path(source).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        businesses = [dict(row) for row in connection.execute("SELECT id, name FROM businesses")]
        services = [dict(row) for row in connection.execute("SELECT business_id, name, price_crc FROM services")]
        appointments = [dict(row) for row in connection.execute("SELECT business_id, customer_name, starts_at FROM appointments")]
    source_ids = {row["id"] for row in businesses}
    if len(source_ids) != len(businesses):
        raise ValueError("Hay empresas históricas duplicadas")
    service_keys = [(row["business_id"], row["name"]) for row in services]
    if len(set(service_keys)) != len(service_keys):
        raise ValueError("Hay servicios históricos duplicados")
    seen = set()
    for row in appointments:
        stamp = datetime.fromisoformat(row["starts_at"])
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("Hay una reserva histórica sin zona horaria")
        row["starts_at"] = stamp.astimezone(timezone.utc)
        row["customer_name"] = row["customer_name"].strip()
        if not 1 <= len(row["customer_name"]) <= 100:
            raise ValueError("Hay una reserva histórica con nombre inválido")
        key = (row["business_id"], row["starts_at"])
        if key in seen:
            raise ValueError("Hay reservas históricas duplicadas por empresa e instante")
        seen.add(key)
    if any(row["business_id"] not in source_ids for row in services + appointments):
        raise ValueError("La fuente contiene referencias a empresas inexistentes")

    with session_factory.begin() as session:
        if not apply and session.get_bind().dialect.name == "postgresql":
            session.execute(text("SET TRANSACTION READ ONLY"))
        new_businesses, new_services, new_appointments = [], [], []
        for row in businesses:
            existing = session.get(Business, row["id"])
            if existing is None:
                new_businesses.append(Business(**row))
            elif existing.name != row["name"]:
                raise ValueError("Una empresa existente tiene datos distintos; requiere revisión")
        for row in services:
            existing = session.scalars(select(Service).where(Service.business_id == row["business_id"], Service.name == row["name"])).all()
            if len(existing) > 1 or (existing and existing[0].price_crc != row["price_crc"]):
                raise ValueError("Un servicio existente presenta un conflicto; requiere revisión")
            if not existing:
                new_services.append(Service(**row))
        for row in appointments:
            existing = session.scalar(select(Appointment).where(Appointment.business_id == row["business_id"], Appointment.starts_at == row["starts_at"]))
            if existing is None:
                new_appointments.append(Appointment(**row))
            elif existing.customer_name != row["customer_name"]:
                raise ValueError("Un horario ya está reservado con datos distintos; requiere revisión")
        summary = {"mode": "apply" if apply else "dry-run", "businesses": len(new_businesses),
                   "services": len(new_services), "appointments": len(new_appointments)}
        if apply:
            session.add_all(new_businesses)
            session.flush()
            session.add_all(new_services + new_appointments)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    from app.database import SessionLocal, engine
    try:
        print(json.dumps(transfer(args.source, SessionLocal, args.apply)))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        print("No se pudo completar el traslado; no se muestran detalles de conexión ni datos personales.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
