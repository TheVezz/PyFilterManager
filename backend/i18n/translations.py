import gettext
from collections.abc import Sequence
from pathlib import Path

from backend.i18n.locale import get_language

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
DOMAIN = "filtri"

_translations: gettext.NullTranslations | gettext.GNUTranslations | None = None


def init_translations() -> gettext.NullTranslations | gettext.GNUTranslations:
    global _translations
    language = get_language()
    try:
        _translations = gettext.translation(
            DOMAIN,
            localedir=str(LOCALES_DIR),
            languages=[language],
            fallback=True,
        )
    except OSError:
        _translations = gettext.NullTranslations()
    return _translations


def _get_translations() -> gettext.NullTranslations | gettext.GNUTranslations:
    if _translations is None:
        return init_translations()
    return _translations


def tr(key: str, /, **kwargs: object) -> str:
    text = _get_translations().gettext(key)
    if kwargs:
        return text.format(**kwargs)
    return text


def filter_state_options() -> list[tuple[str, str]]:
    return [
        ("all", tr("filter.all")),
        ("ok", tr("filter.ok")),
        ("warning", tr("filter.warning")),
        ("overdue", tr("filter.overdue")),
    ]


def report_title(states: Sequence[str]) -> str:
    if states == ["all"]:
        return tr("report.title.all")
    if len(states) == 1:
        return tr(f"report.title.{states[0]}")
    labels = " + ".join(tr(f"report.title.short.{state}") for state in states)
    return tr("report.title.combined", labels=labels)
