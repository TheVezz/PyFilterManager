"""Accesso alla configurazione dell'applicazione."""

import sys
from pathlib import Path

from backend.settings import PYPROJECT_PATH, get_settings


def get_database_path() -> Path:
    return get_settings().sqlite_database_path


def get_database_url() -> str:
    return get_settings().resolved_database_url()


def is_sqlite_url(url: str | None = None) -> bool:
    return (url or get_database_url()).startswith("sqlite")


def get_alembic_config():
    from alembic.config import Config

    return Config(toml_file=str(PYPROJECT_PATH))


def get_app_name() -> str:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with PYPROJECT_PATH.open("rb") as handle:
        data = tomllib.load(handle)

    display_name = data.get("tool", {}).get("filtri", {}).get("display_name")
    if isinstance(display_name, str) and display_name.strip():
        return display_name.strip()

    name = data.get("project", {}).get("name", "filtri")
    if not isinstance(name, str) or not name.strip():
        return "Filtri"
    return name.replace("-", " ").replace("_", " ").title()
