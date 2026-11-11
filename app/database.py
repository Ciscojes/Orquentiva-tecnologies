"""Conexión a la base de datos.

DATABASE_URL tiene prioridad. Sin ella se usa el PostgreSQL local de desarrollo con
POSTGRES_PASSWORD del archivo .env. Si falta la configuración, importar la aplicación
no falla: el error aparece al abrir la primera conexión, con un mensaje claro.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

MISSING = "Falta configurar la base de datos: define DATABASE_URL o POSTGRES_PASSWORD en el archivo .env"

if not os.getenv("DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def make_engine(url, password):
    if url:
        return create_engine(url, pool_pre_ping=True)
    if not password:
        def refuse():
            raise RuntimeError(MISSING)
        return create_engine("postgresql+psycopg://", creator=refuse, pool_pre_ping=True)
    local = URL.create(drivername="postgresql+psycopg", username="orqentiva", password=password,
                       host="127.0.0.1", port=5434, database="orqentiva_db")
    return create_engine(local, pool_pre_ping=True)


engine = make_engine(os.getenv("DATABASE_URL"), os.getenv("POSTGRES_PASSWORD"))

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    with SessionLocal() as session:
        yield session
