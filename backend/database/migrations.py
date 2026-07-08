"""Operazioni sul database tramite Alembic."""

from alembic import command

from backend.config import get_alembic_config


def _config():
    return get_alembic_config()


def upgrade_database() -> None:
    command.upgrade(_config(), "head")


def downgrade_database(revision: str = "-1") -> None:
    command.downgrade(_config(), revision)


def current_revision() -> None:
    command.current(_config())


def create_revision(message: str, *, autogenerate: bool = False) -> None:
    command.revision(_config(), message=message, autogenerate=autogenerate)
