"""Verifica la cadena Alembic contra SQLite temporal, nunca PostgreSQL real."""
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import inspect

from app.database import engine
from app.models import Base


def test_upgrade_matches_models_and_downgrade():
    config = Config("alembic.ini")
    assert engine.dialect.name == "sqlite"
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
