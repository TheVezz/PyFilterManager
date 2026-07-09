from datetime import date
from typing import Literal, cast

from pydantic import Field

from backend.schemas.hierarchy import AppSchema
from backend.schemas.stato_filtro import FiltroStato


class FiltroCard(AppSchema):
    filtro_id: int = Field(gt=0)
    quadro_elettrico_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    reparto: str = Field(min_length=1)
    impianto: str = Field(min_length=1)
    quantita_filtri: int = Field(gt=0)
    dimensione_filtri: str = Field(min_length=1)
    frequenza_intervento: str = Field(min_length=1)
    ultimo_intervento: date | None = None
    stato: FiltroStato


class InterventoVoce(AppSchema):
    intervento_id: int = Field(gt=0)
    data: date
    note: str = ""


class InterventoCreate(AppSchema):
    filtro_id: int = Field(gt=0)
    data: date
    note: str = ""


class InterventoUpdate(AppSchema):
    intervento_id: int = Field(gt=0)
    data: date
    note: str = ""


class QuadroFiltroDetail(AppSchema):
    quadro_elettrico_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    sede: str = Field(min_length=1)
    reparto: str = Field(min_length=1)
    impianto: str = Field(min_length=1)
    impianto_id: int = Field(gt=0)
    filtro_id: int | None = None
    quantita_filtri: int | None = None
    dimensione_filtri: str | None = None
    frequenza_intervento: str | None = None
    preavviso_descrizione: str | None = None
    ultimo_intervento: date | None = None
    prossima_scadenza: date | None = None
    giorni_rimanenti: int | None = None
    giorni_preavviso: int | None = None
    data_inizio_preavviso: date | None = None
    stato: FiltroStato
    interventi: list[InterventoVoce] = Field(default_factory=list)


class ImpiantoFiltriSection(AppSchema):
    impianto_id: int = Field(gt=0)
    impianto: str = Field(min_length=1)
    filtri: list[FiltroCard] = Field(default_factory=list)


class RepartoFiltriSection(AppSchema):
    reparto_id: int = Field(gt=0)
    reparto: str = Field(min_length=1)
    impianti: list[ImpiantoFiltriSection] = Field(default_factory=list)


class RepartoFiltriView(AppSchema):
    reparto_id: int = Field(gt=0)
    reparto: str = Field(min_length=1)
    impianti: list[ImpiantoFiltriSection] = Field(default_factory=list)


class SedeFiltriView(AppSchema):
    sede_id: int = Field(gt=0)
    sede: str = Field(min_length=1)
    reparti: list[RepartoFiltriSection] = Field(default_factory=list)


class ReportQuadroVoce(AppSchema):
    quadro_elettrico_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    reparto: str = Field(min_length=1)
    impianto: str = Field(min_length=1)
    dimensione_filtri: str = Field(min_length=1)
    quantita_filtri: int = Field(gt=0)
    frequenza_intervento: str = Field(min_length=1)
    ultimo_intervento: date | None = None
    data_nuovo_intervento: date | None = None
    stato: FiltroStato
    giorni_scaduto: int | None = None
    giorni_rimanenti: int | None = None


ReportFilterState = Literal["all", "ok", "warning", "overdue"]


class ReportDimensioneVoce(AppSchema):
    dimensione_filtri: str = Field(min_length=1)
    quantita_filtri: int = Field(gt=0)


class ReportSummary(AppSchema):
    states: list[ReportFilterState] = Field(
        default_factory=lambda: cast(list[ReportFilterState], ["all"])
    )
    title: str = Field(min_length=1)
    last_column_title: str = ""
    quadri_scaduti: int = Field(ge=0)
    quadri_ok: int = Field(ge=0)
    quadri_overdue: int = Field(ge=0)
    quadri_warning: int = Field(ge=0)
    filtri_da_preparare: int = Field(ge=0)
    filtri_per_dimensione: list[ReportDimensioneVoce] = Field(default_factory=list)
    quadri_scaduti_voci: list[ReportQuadroVoce] = Field(default_factory=list)


class HomeStatusSummary(AppSchema):
    ok: int = Field(ge=0)
    warning: int = Field(ge=0)
    overdue: int = Field(ge=0)
