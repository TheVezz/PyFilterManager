"""Helper per generare dati di test coerenti con la logica di dominio."""

from datetime import date, timedelta
from typing import Any, cast

from backend.schemas.stato_filtro import (
    FiltroStato,
    StatoFiltroConfig,
    get_stato_filtro_config,
)
from backend.services.stato_filtro_service import calcola_stato_filtro

FREQUENZE_VALIDHE: tuple[str, ...] = (
    "30 giorni",
    "2 settimane",
    "2 mesi",
    "6 mesi",
    "12 mesi",
    "bimestrale",
    "trimestrale",
    "semestrale",
    "annuale",
)

DIMENSIONI_VALIDHE: tuple[str, ...] = (
    "300x300",
    "500x500",
    "600x600",
    "800x800",
    "1000x1000",
)


def assert_quadro_senza_filtro(quadro_elettrico) -> None:
    if getattr(quadro_elettrico, "filtri", []):
        raise ValueError(
            f"Il quadro '{quadro_elettrico.quadro_elettrico}' ha già un filtro associato."
        )


def data_ultimo_intervento_per_stato(
    stato: FiltroStato,
    frequenza_intervento: str,
    oggi: date | None = None,
    config: StatoFiltroConfig | None = None,
) -> date:
    """Trova una data di ultimo intervento che produce lo stato richiesto."""
    oggi = oggi or date.today()
    config = config or get_stato_filtro_config()

    for giorni_indietro in range(0, 3650):
        candidato = oggi - timedelta(days=giorni_indietro)
        if (
            calcola_stato_filtro(candidato, frequenza_intervento, oggi, config)
            == stato
        ):
            return candidato

    raise ValueError(
        f"Impossibile trovare una data per stato {stato!r} "
        f"con frequenza {frequenza_intervento!r}"
    )


def _aggiungi_storico_interventi(filtro, storico_interventi: int) -> None:
    if storico_interventi <= 0 or not filtro.interventi:
        return

    from backend.factories.factories import InterventoFactory

    ultimo = max(intervento.data for intervento in filtro.interventi)
    for indice in range(1, storico_interventi + 1):
        InterventoFactory(
            filtro=filtro,
            data=ultimo - timedelta(days=365 * indice),
            note=f"Intervento storico {indice}",
        )


def crea_quadro_con_filtro(
    *,
    linea,
    quadro_elettrico: str,
    quantita_filtri: int,
    dimensione_filtri: str,
    frequenza_intervento: str,
    stato: FiltroStato | None = None,
    storico_interventi: int = 0,
):
    """Crea un quadro elettrico con il suo unico filtro."""
    from backend.factories.factories import QuadroElettricoFactory

    quadro = QuadroElettricoFactory(
        linea=linea,
        quadro_elettrico=quadro_elettrico,
        quantita_filtri=quantita_filtri,
        dimensione_filtri=dimensione_filtri,
        frequenza_intervento=frequenza_intervento,
        stato=stato,
    )
    filtri = getattr(quadro, "filtri", [])
    if storico_interventi > 0 and filtri:
        _aggiungi_storico_interventi(cast(Any, filtri[0]), storico_interventi)
    return quadro


def crea_filtro_con_stato(
    *,
    quadro_elettrico,
    quantita_filtri: int,
    dimensione_filtri: str,
    frequenza_intervento: str,
    stato: FiltroStato | None = None,
    storico_interventi: int = 0,
):
    """Aggiunge l'unico filtro consentito a un quadro esistente."""
    from backend.factories.factories import FiltroFactory

    assert_quadro_senza_filtro(quadro_elettrico)
    filtro = FiltroFactory(
        quadro_elettrico=quadro_elettrico,
        quantita_filtri=quantita_filtri,
        dimensione_filtri=dimensione_filtri,
        frequenza_intervento=frequenza_intervento,
        stato=stato,
    )
    _aggiungi_storico_interventi(filtro, storico_interventi)
    return filtro
