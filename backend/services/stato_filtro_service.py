"""Calcolo stato filtro in base a ultimo intervento e frequenza."""

from datetime import date
from math import ceil

from backend.schemas.frequenza import aggiungi_frequenza
from backend.schemas.stato_filtro import (
    FiltroStato,
    StatoFiltroConfig,
    get_stato_filtro_config,
)


def calcola_scadenza_intervento(
    ultimo_intervento: date,
    frequenza_intervento: str,
) -> date:
    return aggiungi_frequenza(ultimo_intervento, frequenza_intervento)


def _giorni_preavviso(
    ultimo_intervento: date,
    scadenza: date,
    config: StatoFiltroConfig,
) -> int:
    periodo_giorni = (scadenza - ultimo_intervento).days
    if periodo_giorni <= 0:
        return 0
    da_percentuale = ceil(periodo_giorni * config.preavviso_percentuale / 100)
    return max(1, min(da_percentuale, config.preavviso_massimo_giorni))


def calcola_giorni_preavviso(
    ultimo_intervento: date,
    scadenza: date,
    config: StatoFiltroConfig | None = None,
) -> int:
    config = config or get_stato_filtro_config()
    return _giorni_preavviso(ultimo_intervento, scadenza, config)


def calcola_stato_filtro(
    ultimo_intervento: date | None,
    frequenza_intervento: str,
    oggi: date | None = None,
    config: StatoFiltroConfig | None = None,
) -> FiltroStato:
    config = config or get_stato_filtro_config()
    reference = oggi or date.today()

    if ultimo_intervento is None:
        return "overdue"

    scadenza = calcola_scadenza_intervento(ultimo_intervento, frequenza_intervento)
    giorni_rimanenti = (scadenza - reference).days

    if giorni_rimanenti < 0:
        return "overdue"

    preavviso = _giorni_preavviso(ultimo_intervento, scadenza, config)
    if giorni_rimanenti <= preavviso:
        return "warning"
    return "ok"
