"""Risoluzione configurazione preavviso per filtro."""

from backend.models.filtro import Filtro
from backend.schemas.stato_filtro import StatoFiltroConfig, get_stato_filtro_config


def config_preavviso_per_filtro(filtro: Filtro | None) -> StatoFiltroConfig:
    config = get_stato_filtro_config()
    if filtro is None or filtro.preavviso_usa_globale:
        return config

    return StatoFiltroConfig(
        preavviso_percentuale=filtro.preavviso_percentuale or config.preavviso_percentuale,
        preavviso_massimo_giorni=filtro.preavviso_massimo_giorni or config.preavviso_massimo_giorni,
    )


def descrizione_preavviso_filtro(filtro: Filtro | None) -> str:
    config = config_preavviso_per_filtro(filtro)
    if filtro is None or filtro.preavviso_usa_globale:
        return (
            f"Globale ({config.preavviso_percentuale:g}%, "
            f"max {config.preavviso_massimo_giorni} giorni)"
        )
    return (
        f"Personalizzato ({config.preavviso_percentuale:g}%, "
        f"max {config.preavviso_massimo_giorni} giorni)"
    )
