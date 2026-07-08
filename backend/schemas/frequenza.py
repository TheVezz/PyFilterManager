import calendar
import re
from datetime import date, timedelta

FREQUENZA_ALIASES: dict[str, str] = {
    "bimestrale": "2 mesi",
    "trimestrale": "3 mesi",
    "quadrimestrale": "4 mesi",
    "semestrale": "6 mesi",
    "annuale": "12 mesi",
}

FREQUENZA_PATTERN = re.compile(
    r"^(\d+)\s+(giorni|giorno|settimane|settimana|mesi|mese)$",
    re.IGNORECASE,
)

FREQUENZA_ERROR_MESSAGE = (
    "Usa un numero seguito da giorni, settimane o mesi "
    "(es. 30 giorni, 2 settimane, 12 mesi) oppure "
    "bimestrale, trimestrale, semestrale, annuale."
)


def normalize_frequenza_intervento(value: str) -> str:
    text = value.strip().lower()
    if not text:
        raise ValueError(FREQUENZA_ERROR_MESSAGE)

    if text in FREQUENZA_ALIASES:
        return FREQUENZA_ALIASES[text]

    match = FREQUENZA_PATTERN.match(text)
    if match is None:
        raise ValueError(FREQUENZA_ERROR_MESSAGE)

    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError(FREQUENZA_ERROR_MESSAGE)

    unit = match.group(2).lower()
    if unit in {"giorno", "giorni"}:
        label = "giorno" if amount == 1 else "giorni"
    elif unit in {"settimana", "settimane"}:
        label = "settimana" if amount == 1 else "settimane"
    else:
        label = "mese" if amount == 1 else "mesi"

    return f"{amount} {label}"


def _parse_frequenza(frequenza: str) -> tuple[int, str]:
    normalized = normalize_frequenza_intervento(frequenza)
    amount = int(normalized.split()[0])
    unit = normalized.split()[1]
    return amount, unit


def aggiungi_mesi(start: date, months: int) -> date:
    """Aggiunge mesi di calendario, adattando il giorno se necessario."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, max_day))


def aggiungi_frequenza(start: date, frequenza: str) -> date:
    amount, unit = _parse_frequenza(frequenza)

    if unit.startswith("giorn"):
        return start + timedelta(days=amount)
    if unit.startswith("settiman"):
        return start + timedelta(weeks=amount)
    return aggiungi_mesi(start, amount)
