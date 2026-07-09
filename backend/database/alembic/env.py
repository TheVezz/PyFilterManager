from alembic import context
from sqlalchemy import create_engine, pool

from backend.config import is_sqlite_url
from backend.database.db_manager import DATABASE_URL
from backend.models import (  # noqa: F401
    Base,
    Filtro,
    Impianto,
    Intervento,
    QuadroElettrico,
    Reparto,
    Sede,
)

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite_url(DATABASE_URL),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite_url(DATABASE_URL),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
