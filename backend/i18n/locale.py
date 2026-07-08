from __future__ import annotations

import locale
from dataclasses import dataclass

from PySide6.QtCore import QLocale

from backend.schemas.app_preferences import (
    DEFAULT_APP_PREFERENCES,
    AppPreferences,
    DateFormatPreference,
    LanguagePreference,
)

SUPPORTED_LANGUAGES = frozenset({"it", "en"})
DEFAULT_LANGUAGE = "it"
DEFAULT_BABEL_LOCALE = "it_IT"


@dataclass(frozen=True)
class LocaleSettings:
    language: str
    babel_locale: str
    qlocale: QLocale
    language_preference: LanguagePreference
    date_format_preference: DateFormatPreference


_settings: LocaleSettings | None = None
_active_preferences: AppPreferences = DEFAULT_APP_PREFERENCES.model_copy()


def _normalize_qlocale_name(qlocale: QLocale) -> str:
    return qlocale.name().replace("-", "_")


def _language_code_from_tag(tag: str) -> str | None:
    code = tag.split("-")[0].lower()
    if code in SUPPORTED_LANGUAGES:
        return code
    return None


def _language_from_ui_languages(qlocale: QLocale) -> str | None:
    for tag in qlocale.uiLanguages():
        code = _language_code_from_tag(tag)
        if code is not None:
            return code
    return None


def _language_from_python_locale() -> str | None:
    try:
        current = locale.getlocale()[0]
        if current:
            return _language_code_from_tag(current.replace("_", "-"))
    except locale.Error:
        return None
    return None


def _detect_system_language() -> str:
    system_qlocale = QLocale.system()
    locale_name = _normalize_qlocale_name(system_qlocale)
    return (
        _language_from_ui_languages(system_qlocale)
        or _language_code_from_tag(locale_name)
        or _language_from_python_locale()
        or DEFAULT_LANGUAGE
    )


def _resolve_babel_locale(locale_name: str, language: str) -> str:
    if language == "it":
        return "it_IT"
    if language == "en":
        if locale_name.startswith("en_GB"):
            return "en_GB"
        return "en_US"
    if locale_name.startswith("it_"):
        return "it_IT"
    if locale_name.startswith("en_"):
        return locale_name
    return DEFAULT_BABEL_LOCALE


def _resolve_ui_qlocale(language: str, locale_name: str) -> QLocale:
    if language == "it":
        return QLocale(QLocale.Language.Italian, QLocale.Country.Italy)
    if locale_name.startswith("en_GB"):
        return QLocale(QLocale.Language.English, QLocale.Country.UnitedKingdom)
    return QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)


def _resolve_language(preference: LanguagePreference) -> str:
    if preference == "system":
        return _detect_system_language()
    return preference


def resolve_locale(preferences: AppPreferences | None = None) -> LocaleSettings:
    prefs = preferences or _active_preferences
    system_qlocale = QLocale.system()
    locale_name = _normalize_qlocale_name(system_qlocale)
    language = _resolve_language(prefs.language)

    return LocaleSettings(
        language=language,
        babel_locale=_resolve_babel_locale(locale_name, language),
        qlocale=_resolve_ui_qlocale(language, locale_name),
        language_preference=prefs.language,
        date_format_preference=prefs.date_format,
    )


def detect_locale() -> LocaleSettings:
    return resolve_locale(DEFAULT_APP_PREFERENCES)


def init_locale(preferences: AppPreferences | None = None) -> LocaleSettings:
    global _settings, _active_preferences
    if preferences is not None:
        _active_preferences = preferences.model_copy()
    _settings = resolve_locale(_active_preferences)
    return _settings


def reload_locale(preferences: AppPreferences | None = None) -> LocaleSettings:
    return init_locale(preferences)


def get_settings() -> LocaleSettings:
    if _settings is None:
        return init_locale()
    return _settings


def get_active_preferences() -> AppPreferences:
    return _active_preferences.model_copy()


def get_language() -> str:
    return get_settings().language


def get_babel_locale() -> str:
    return get_settings().babel_locale


def get_qlocale() -> QLocale:
    return get_settings().qlocale


def get_date_format_preference() -> DateFormatPreference:
    return get_settings().date_format_preference
