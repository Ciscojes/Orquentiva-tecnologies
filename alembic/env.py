
from logging.config import fileConfig

from alembic import context

from app.database import engine
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tablas definidas en nuestros modelos ORM
target_metadata = Base.metadata


def run_migrations_offline():
    """Genera SQL sin ejecutar la migración."""
    url = engine.url.render_as_string(
        hide_password=False
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Ejecuta migraciones usando PostgreSQL."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
