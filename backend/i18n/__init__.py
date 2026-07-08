from backend.i18n.dates import (
    EMPTY_VALUE,
    date_input_placeholder,
    format_date,
    format_datetime,
    invalid_date_message,
    parse_user_date,
)
from backend.i18n.locale import (
    get_active_preferences,
    get_babel_locale,
    get_date_format_preference,
    get_language,
    get_qlocale,
    init_locale,
    reload_locale,
)
from backend.i18n.translations import (
    filter_state_options,
    init_translations,
    report_title,
    tr,
)
from backend.services.app_preferences_service import load_app_preferences
from backend.services.app_theme_service import apply_app_preferences, apply_theme


def init_i18n(app=None) -> None:
    apply_app_preferences(load_app_preferences(), app=app)


__all__ = [
    "EMPTY_VALUE",
    "apply_app_preferences",
    "apply_theme",
    "date_input_placeholder",
    "filter_state_options",
    "format_date",
    "format_datetime",
    "get_active_preferences",
    "get_babel_locale",
    "get_date_format_preference",
    "get_language",
    "get_qlocale",
    "init_i18n",
    "init_locale",
    "init_translations",
    "invalid_date_message",
    "parse_user_date",
    "reload_locale",
    "report_title",
    "tr",
]
