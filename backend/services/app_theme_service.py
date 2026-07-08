from qfluentwidgets import FluentTranslator, Theme, setTheme

from backend.i18n.locale import get_qlocale, reload_locale
from backend.i18n.translations import init_translations
from backend.schemas.app_preferences import AppPreferences, ThemePreference
from backend.services.app_preferences_service import load_app_preferences


def theme_from_preference(preference: ThemePreference) -> Theme:
    mapping = {
        "auto": Theme.AUTO,
        "light": Theme.LIGHT,
        "dark": Theme.DARK,
    }
    return mapping[preference]


def apply_theme(preference: ThemePreference) -> None:
    setTheme(theme_from_preference(preference), save=False)


def apply_app_preferences(
    preferences: AppPreferences | None = None,
    *,
    app=None,
) -> AppPreferences:
    prefs = preferences or load_app_preferences()
    reload_locale(prefs)
    init_translations()
    apply_theme(prefs.theme)

    if app is not None:
        old_translator = getattr(app, "_filtri_fluent_translator", None)
        if old_translator is not None:
            app.removeTranslator(old_translator)
        translator = FluentTranslator(get_qlocale())
        app._filtri_fluent_translator = translator
        app.installTranslator(translator)

    return prefs
