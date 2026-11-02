"""Comprueba la integración en un PostgreSQL temporal e independiente.

No utiliza .env ni conecta con el servidor PostgreSQL habitual del proyecto.
Requiere los binarios locales de PostgreSQL (initdb y pg_ctl).
"""
import argparse
from contextlib import closing
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import sqlite3
from concurrent.futures import ThreadPoolExecutor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-bin", type=Path, default=Path(r"C:\Program Files\PostgreSQL\17\bin"))
    args = parser.parse_args()
    suffix = ".exe" if os.name == "nt" else ""
    def binary(name):
        candidate = args.postgres_bin / (name + suffix)
        path = str(candidate) if candidate.is_file() else shutil.which(name)
        if not path:
            raise RuntimeError(f"No se encuentra {name}; indica --postgres-bin")
        return path
    initdb, pg_ctl = binary("initdb"), binary("pg_ctl")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    def run(arguments):
        # Un proceso servidor puede heredar pipes y mantener communicate() abierto.
        with tempfile.TemporaryFile(mode="w+b") as output:
            result = subprocess.run(arguments, stdin=subprocess.DEVNULL, stdout=output,
                                    stderr=subprocess.STDOUT, creationflags=flags, timeout=120)
            if result.returncode:
                output.seek(0)
                raise RuntimeError(f"Falló {Path(arguments[0]).name}: {output.read().decode(errors='replace')}")

    with tempfile.TemporaryDirectory(prefix="orqentiva-pg-qa-") as folder:
        path = Path(folder)
        data = path / "data"
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
        run([initdb, "-D", str(data), "-U", "qa", "--auth=trust", "--encoding=UTF8", "--no-locale"])
        started = False
        engine = None
        try:
            run([pg_ctl, "-D", str(data), "-l", str(path / "postgres.log"), "-o", f"-h 127.0.0.1 -p {port}", "-w", "start"])
            started = True
            os.environ["DATABASE_URL"] = f"postgresql+psycopg://qa@127.0.0.1:{port}/postgres"
            os.environ["ORQENTIVA_DB"] = str(path / "demo.sqlite3")
            root = Path(__file__).resolve().parents[1]
            sys.path.insert(0, str(root))
            os.chdir(root)
            from alembic import command
            from alembic.config import Config
            from alembic.autogenerate import compare_metadata
            from alembic.migration import MigrationContext
            from fastapi.testclient import TestClient
            from sqlalchemy import select
            from app.database import engine, SessionLocal
            from app.main import app
            from app.models import Appointment, Base, Lead
            from seed import seed_database

            config = Config(str(root / "alembic.ini"))
            command.upgrade(config, "head")
            with engine.connect() as connection:
                assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            print("OK: migraciones PostgreSQL y modelos coinciden")
            seed_database()
            seed_database()
            with TestClient(app) as client:
                for key, business in [("demo-barberia-alfa", "alfa"), ("demo-barberia-beta", "beta")]:
                    response = client.get("/business/me", headers={"X-API-Key": key})
                    assert response.status_code == 200 and response.json()["id"] == business
                print("OK: empresas demo y seed repetible")
                alfa = {"X-API-Key": "demo-barberia-alfa"}
                beta = {"X-API-Key": "demo-barberia-beta"}
                assert client.get("/services", headers=alfa).json()[0]["name"] == "Corte clásico"
                assert client.get("/services", headers=beta).json()[0]["name"] == "Corte premium"
                def book(stamp, headers=alfa):
                    return client.post("/appointments", headers=headers,
                        json={"customer_name": "QA PostgreSQL", "starts_at": stamp})
                with ThreadPoolExecutor(max_workers=2) as pool:
                    responses = list(pool.map(lambda stamp: book(stamp).status_code,
                        ["2032-01-01T12:00:00-06:00", "2032-01-01T18:00:00Z"]))
                assert sorted(responses) == [201, 409]
                assert client.get("/appointments", headers=beta).json() == []
                assert book("2032-01-01T18:00:00Z", beta).status_code == 201
                for stamp in ["2032-01-01T18:00:00.000001Z", "2032-01-01T18:00:00.000002Z"]:
                    assert book(stamp).status_code == 201
                rows = client.get("/appointments", headers=alfa).json()
                assert len(rows) == 3
                assert rows[0]["starts_at"] == "2032-01-01T18:00:00+00:00"
                assert rows[-1]["starts_at"] == "2032-01-01T18:00:00.000002+00:00"
                with SessionLocal() as session:
                    appointments = session.scalars(select(Appointment)).all()
                    assert len(appointments) == 4
                    assert all(row.starts_at.utcoffset() is not None for row in appointments)
                assert book("2032-01-01T18:00:00").status_code == 422
                assert client.post("/appointments", headers=alfa,
                    json={"customer_name": "   ", "starts_at": "2033-01-01T18:00:00Z"}).status_code == 422
                assert not (path / "demo.sqlite3").exists()
                print("OK: servicios y reservas PostgreSQL, concurrencia, aislamiento, UTC y microsegundos")
                from scripts.import_legacy_sqlite import transfer
                legacy = path / "legacy.sqlite3"
                with closing(sqlite3.connect(legacy)) as connection, connection:
                    connection.executescript("""
                        CREATE TABLE businesses (id TEXT, name TEXT);
                        CREATE TABLE services (business_id TEXT, name TEXT, price_crc INTEGER);
                        CREATE TABLE appointments (business_id TEXT, customer_name TEXT, starts_at TEXT);
                        INSERT INTO businesses VALUES ('alfa', 'Barbería Alfa');
                        INSERT INTO services VALUES ('alfa', 'Corte clásico', 5000);
                        INSERT INTO appointments VALUES ('alfa', 'QA Histórico', '2034-01-01T12:00:00-06:00');
                    """)
                assert transfer(legacy, SessionLocal)["appointments"] == 1
                assert transfer(legacy, SessionLocal, apply=True)["appointments"] == 1
                assert transfer(legacy, SessionLocal, apply=True)["appointments"] == 0
                assert len(client.get("/appointments", headers=alfa).json()) == 4
                print("OK: simulación y traslado histórico idempotente en PostgreSQL temporal")
                payload = {"name": "QA PostgreSQL", "email": "qa@example.com", "service": "agents", "message": "Solicitud ficticia de integración."}
                response = client.post("/leads", json=payload)
                assert response.status_code == 201 and response.json() == {"status": "created"}
                with SessionLocal() as session:
                    lead = session.scalars(select(Lead)).one()
                    assert lead.name == payload["name"] and lead.email == payload["email"]
                    assert lead.created_at is not None and lead.created_at.utcoffset() is not None
                print("OK: POST /leads persiste y genera fecha con zona horaria")
                assert client.post("/leads", json={**payload, "email": "incorrecto"}).status_code == 422
                assert client.get("/leads").status_code == 405
                print("OK: validación y ausencia de listado público")
                for _ in range(4):
                    assert client.post("/leads", json=payload).status_code == 201
                assert client.post("/leads", json=payload).status_code == 429
                with SessionLocal() as session:
                    assert len(session.scalars(select(Lead)).all()) == 5
                print("OK: límite de envíos sin filas adicionales")
            command.downgrade(config, "base")
            print("OK: downgrade PostgreSQL completo")
        finally:
            if engine is not None:
                engine.dispose()
            if started:
                run([pg_ctl, "-D", str(data), "-m", "fast", "-w", "stop"])
    print("Integración PostgreSQL aprobada; servidor temporal detenido.")


if __name__ == "__main__":
    main()
