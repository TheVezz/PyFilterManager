"""Compatibilità: configurazione in backend.schemas.settings."""

from backend.schemas.settings import (
    APP_ROOT,
    ENV_PATH,
    PYPROJECT_PATH,
    Settings,
    get_settings,
)

__all__ = ["APP_ROOT", "ENV_PATH", "PYPROJECT_PATH", "Settings", "get_settings"]
