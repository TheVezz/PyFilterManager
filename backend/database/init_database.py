"""Applica le migrazioni Alembic al database."""

from backend.database.migrations import upgrade_database


def init_database() -> None:
    upgrade_database()
