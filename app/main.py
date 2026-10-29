"""ORQENTIVA AI: primer corte vertical educativo de una API multiempresa.

ADVERTENCIA: credenciales de DEMOSTRACIÓN; no publicar así en Internet.
"""
import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

DB_PATH = os.getenv("ORQENTIVA_DB", str(Path(__file__).parent.parent / "orqentiva.db"))
DEMO_KEYS = {"demo-barberia-alfa": "alfa", "demo-barberia-beta": "beta"}




@contextmanager
def database():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with database() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY, name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL REFERENCES businesses(id),
            name TEXT NOT NULL, price_crc INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL REFERENCES businesses(id),
            customer_name TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            UNIQUE(business_id, starts_at)
        );
        """)
        for bid, name in [("alfa", "Barbería Alfa"), ("beta", "Barbería Beta")]:
            conn.execute("INSERT OR IGNORE INTO businesses(id,name) VALUES (?,?)", (bid,name))
        for bid, service, price in [("alfa", "Corte clásico", 5000), ("beta", "Corte premium", 8500)]:
            exists = conn.execute("SELECT 1 FROM services WHERE business_id=? AND name=?",(bid,service)).fetchone()
            if not exists:
                conn.execute("INSERT INTO services(business_id,name,price_crc) VALUES (?,?,?)",(bid,service,price))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="ORQENTIVA AI", version="0.1.0", description="API educativa multiempresa", lifespan=lifespan)


def current_business(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key or x_api_key not in DEMO_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key de demostración inválida")
    return DEMO_KEYS[x_api_key]


class AppointmentIn(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    starts_at: datetime


@app.get("/health")
def health():
    return {"status": "ok", "project": "ORQENTIVA AI", "version": "0.1.0"}


@app.get("/business/me")
def my_business(business_id: Annotated[str, Depends(current_business)]):
    with database() as conn:
        record = conn.execute("SELECT id, name FROM businesses WHERE id=?", (business_id,)).fetchone()
        return dict(record)


@app.get("/services")
def services(business_id: Annotated[str, Depends(current_business)]):
    with database() as conn:
        rows = conn.execute("SELECT id, name, price_crc FROM services WHERE business_id=?",(business_id,)).fetchall()
        return [dict(r) for r in rows]


@app.get("/appointments")
def appointments(business_id: Annotated[str, Depends(current_business)]):
    with database() as conn:
        rows = conn.execute("SELECT id, customer_name, starts_at FROM appointments WHERE business_id=? ORDER BY starts_at", (business_id,)).fetchall()
        return [dict(r) for r in rows]


@app.post("/appointments", status_code=201)
def create_appointment(payload: AppointmentIn, business_id: Annotated[str, Depends(current_business)]):
    if payload.starts_at.tzinfo is None or payload.starts_at.utcoffset() is None:
        raise HTTPException(422, "Se requiere fecha con zona horaria (por ejemplo -06:00)")
    starts_at = payload.starts_at.isoformat()
    with database() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO appointments (business_id, customer_name, starts_at) VALUES (?,?,?)",
                (business_id, payload.customer_name.strip(), starts_at),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Horario ya reservado para esta empresa") from None
        return {"id": cursor.lastrowid, "business_id": business_id, "customer_name": payload.customer_name.strip(), "starts_at": starts_at}
