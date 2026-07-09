from __future__ import annotations

import json

from backend.schemas.app_preferences import (
    DEFAULT_APP_PREFERENCES,
    AppPreferences,
    DateFormatPreference,
    LanguagePreference,
    LiveRefreshPreference,
    ThemePreference,
)
from backend.schemas.settings import APP_ROOT

PREFERENCES_PATH = APP_ROOT / "data" / "app_preferences.json"


def _ensure_parent_dir() -> None:
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_app_preferences() -> AppPreferences:
    if not PREFERENCES_PATH.exists():
        return DEFAULT_APP_PREFERENCES.model_copy()

    try:
        data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
        return AppPreferences.model_validate(data)
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_APP_PREFERENCES.model_copy()


def save_app_preferences(preferences: AppPreferences) -> None:
    _ensure_parent_dir()
    PREFERENCES_PATH.write_text(
        preferences.model_dump_json(indent=2),
        encoding="utf-8",
    )


def update_app_preferences(
    *,
    theme: ThemePreference | None = None,
    language: LanguagePreference | None = None,
    date_format: DateFormatPreference | None = None,
    live_refresh_seconds: LiveRefreshPreference | None = None,
) -> AppPreferences:
    current = load_app_preferences()
    updated = current.model_copy(
        update={
            key: value
            for key, value in {
                "theme": theme,
                "language": language,
                "date_format": date_format,
                "live_refresh_seconds": live_refresh_seconds,
            }.items()
            if value is not None
        }
    )
    save_app_preferences(updated)
    return updated
