
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

if not os.getenv("DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

password = os.getenv("POSTGRES_PASSWORD")

if not password and not os.getenv("DATABASE_URL"):
    raise RuntimeError(
        "Falta POSTGRES_PASSWORD en el archivo .env"
    )

DATABASE_URL = os.getenv("DATABASE_URL") or URL.create(
    drivername="postgresql+psycopg",
    username="orqentiva",
    password=password,
    host="127.0.0.1",
    port=5434,
    database="orqentiva_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    with SessionLocal() as session:
        yield session

