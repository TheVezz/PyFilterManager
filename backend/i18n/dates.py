from __future__ import annotations

from datetime import date, datetime

from babel.dates import format_date as babel_format_date
from babel.dates import format_datetime as babel_format_datetime
from babel.dates import parse_date as babel_parse_date

from backend.i18n.locale import (
    get_babel_locale,
    get_date_format_preference,
    get_language,
)
from backend.i18n.translations import tr

EMPTY_VALUE = "—"


def _date_format_pattern() -> str:
    preference = get_date_format_preference()
    if preference == "mdY":
        return "MM/dd/yyyy"
    if preference == "dmY":
        return "dd/MM/yyyy"
    if get_language() == "en" and get_babel_locale().startswith("en_US"):
        return "MM/dd/yyyy"
    return "dd/MM/yyyy"


def format_date(value: date | None) -> str:
    if value is None:
        return EMPTY_VALUE
    return babel_format_date(
        value,
        format=_date_format_pattern(),
        locale=get_babel_locale(),
    )


def format_datetime(value: datetime) -> str:
    return babel_format_datetime(
        value,
        format=f"{_date_format_pattern()} HH:mm",
        locale=get_babel_locale(),
    )


def date_input_placeholder() -> str:
    preference = get_date_format_preference()
    if preference == "mdY":
        return "mm/dd/yyyy"
    if preference == "dmY":
        return "gg/mm/aaaa" if get_language() == "it" else "dd/mm/yyyy"
    if get_language() == "en" and get_babel_locale().startswith("en_US"):
        return "mm/dd/yyyy"
    if get_language() == "it":
        return "gg/mm/aaaa"
    return "dd/mm/yyyy"


def parse_user_date(text: str) -> date | None:
    cleaned = text.strip()
    if not cleaned:
        return None

    try:
        return babel_parse_date(cleaned, locale=get_babel_locale())
    except (ValueError, TypeError, OverflowError):
        pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def invalid_date_message() -> str:
    return tr("date.invalid", format=date_input_placeholder())
