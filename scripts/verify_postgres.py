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
            os.environ["AUTH_COOKIE_SECURE"] = "false"
            os.environ["AUTH_ALLOWED_ORIGINS"] = "http://testserver"
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
            command.upgrade(config, "d8f25b602d7b")
            from sqlalchemy import text as sql_text
            # Preparar datos del esquema anterior sin usar modelos que requieren columnas nuevas.
            with engine.begin() as connection:
                connection.execute(sql_text("INSERT INTO businesses (id, name) VALUES ('alfa', 'Barbería Alfa'), ('beta', 'Barbería Beta')"))
                connection.execute(sql_text("INSERT INTO services (business_id, name, price_crc) VALUES ('alfa', 'Corte clásico', 5000), ('beta', 'Corte premium', 8500)"))
            with engine.connect() as connection:
                before_services = connection.execute(sql_text("SELECT id, business_id, name, price_crc FROM services ORDER BY id")).all()
            command.upgrade(config, "head")
            with engine.connect() as connection:
                assert connection.execute(sql_text("SELECT id, business_id, name, price_crc FROM services ORDER BY id")).all() == before_services
            with engine.connect() as connection:
                assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            print("OK: migraciones PostgreSQL y modelos coinciden")
            seed_database()
            seed_database()
            from app.auth import UserCreate, create_user, COOKIE_NAME, token_digest
            from app.models import AuthSession
            import secrets
            password = secrets.token_urlsafe(24)
            with SessionLocal.begin() as session:
                for name in ["alfa", "beta", "admin"]:
                    create_user(session, UserCreate(email=f"{name}@example.com", password=password,
                        role="super_admin" if name == "admin" else "business_admin",
                        business_id=None if name == "admin" else name))
            with TestClient(app) as client:
                credentials = {}
                for name in ["alfa", "beta", "admin"]:
                    client.cookies.clear()
                    response = client.post("/auth/login", headers={"Origin": "http://testserver"},
                        json={"email": f"{name}@example.com", "password": password})
                    assert response.status_code == 200
                    token = client.cookies[COOKIE_NAME]
                    credentials[name] = {"Cookie": f"{COOKIE_NAME}={token}", "Origin": "http://testserver"}
                    with SessionLocal() as session:
                        row = session.get(AuthSession, token_digest(token))
                        assert row is not None and row.expires_at.utcoffset() is not None
                    if name != "admin":
                        response = client.get("/business/me")
                        assert response.status_code == 200 and response.json()["id"] == name
                client.cookies.clear()
                alfa, beta = credentials["alfa"], credentials["beta"]
                assert client.get("/services", headers={"X-API-Key": "demo-barberia-alfa"}).status_code == 401
                assert client.get("/appointments", headers=credentials["admin"]).status_code == 403
                print("OK: migración conserva datos, cuentas Argon2 y sesiones PostgreSQL por rol")
                admin = credentials["admin"]
                assert len(client.get("/admin/businesses", headers=admin).json()) == 2
                assert all(row["is_active"] for row in client.get("/admin/businesses", headers=admin).json())
                assert client.get("/admin/businesses", headers=alfa).status_code == 403
                assert client.post("/admin/businesses", headers=admin, json={"id":"gamma","name":"Gamma QA"}).status_code == 201
                assert client.post("/admin/businesses", headers=admin, json={"id":"gamma","name":"Otro"}).status_code == 409
                assert client.post("/admin/businesses/gamma/users", headers=admin,
                    json={"email":"gamma@example.com","password":password}).status_code == 201
                assert client.patch("/admin/businesses/gamma", headers=admin, json={"is_active":False}).status_code == 200
                assert client.post("/auth/login",headers={"Origin":"http://testserver"},
                    json={"email":"gamma@example.com","password":password}).status_code == 401
                assert client.patch("/admin/businesses/gamma", headers=admin, json={"is_active":True}).status_code == 200
                assert client.post("/auth/login",headers={"Origin":"http://testserver"},
                    json={"email":"gamma@example.com","password":password}).status_code == 200
                gamma_token = client.cookies[COOKIE_NAME]
                client.cookies.clear()
                assert client.patch("/admin/businesses/gamma", headers=admin, json={"is_active":False}).status_code == 200
                assert client.get("/auth/me",headers={"Cookie":f"{COOKIE_NAME}={gamma_token}"}).status_code == 401
                print("OK: panel administrativo PostgreSQL, creación, permisos y revocación al desactivar")
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
                assert client.post("/auth/logout", headers=alfa).status_code == 204
                assert client.get("/auth/me", headers=alfa).status_code == 401
                assert client.get("/auth/me", headers=beta).status_code == 200
                print("OK: logout revoca una sesión sin afectar al otro negocio")
            command.downgrade(config, "d8f25b602d7b")
            with engine.connect() as connection:
                assert connection.execute(sql_text("SELECT id, business_id, name, price_crc FROM services ORDER BY id")).all() == before_services
            command.upgrade(config, "head")
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
