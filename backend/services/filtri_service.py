from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.db_manager import get_session
from backend.i18n import report_title
from backend.models import Filtro, Linea, QuadroElettrico, Reparto, Sede
from backend.schemas.filtri import (
    FiltroCard,
    HomeStatusSummary,
    InterventoVoce,
    LineaFiltriSection,
    QuadroFiltroDetail,
    RepartoFiltriSection,
    RepartoFiltriView,
    ReportDimensioneVoce,
    ReportFilterState,
    ReportQuadroVoce,
    ReportSummary,
    SedeFiltriView,
)
from backend.services.preavviso_filtro_service import (
    config_preavviso_per_filtro,
    descrizione_preavviso_filtro,
)
from backend.services.stato_filtro_service import (
    calcola_giorni_preavviso,
    calcola_scadenza_intervento,
    calcola_stato_filtro,
)


def _ultimo_intervento(filtro: Filtro):
    if not filtro.interventi:
        return None
    return max(intervento.data for intervento in filtro.interventi)


def _filtro_card(quadro: QuadroElettrico, filtro: Filtro) -> FiltroCard:
    ultimo = _ultimo_intervento(filtro)
    config = config_preavviso_per_filtro(filtro)
    linea = quadro.linea
    reparto = linea.reparto
    return FiltroCard(
        filtro_id=filtro.id,
        quadro_elettrico_id=quadro.id,
        quadro_elettrico=quadro.quadro_elettrico,
        reparto=reparto.reparto,
        linea=linea.linea,
        quantita_filtri=filtro.quantita_filtri,
        dimensione_filtri=filtro.dimensione_filtri,
        frequenza_intervento=filtro.frequenza_intervento,
        ultimo_intervento=ultimo,
        stato=calcola_stato_filtro(
            ultimo,
            filtro.frequenza_intervento,
            config=config,
        ),
    )


def _filtro_cards_from_quadri(quadri: list[QuadroElettrico]) -> list[FiltroCard]:
    cards: list[FiltroCard] = []
    for quadro in sorted(quadri, key=lambda item: item.quadro_elettrico):
        for filtro in sorted(quadro.filtri, key=lambda item: item.quantita_filtri):
            cards.append(_filtro_card(quadro, filtro))
    return cards


def _linea_section(linea: Linea) -> LineaFiltriSection:
    return LineaFiltriSection(
        linea_id=linea.id,
        linea=linea.linea,
        filtri=_filtro_cards_from_quadri(linea.quadri_elettrici),
    )


def load_filtri_by_reparto(reparto_id: int) -> RepartoFiltriView | None:
    with get_session() as session:
        reparto = session.scalar(
            select(Reparto)
            .options(
                selectinload(Reparto.linee)
                .selectinload(Linea.quadri_elettrici)
                .selectinload(QuadroElettrico.filtri)
                .selectinload(Filtro.interventi)
            )
            .where(Reparto.id == reparto_id)
        )
        if reparto is None:
            return None

        linee = [
            _linea_section(linea)
            for linea in sorted(reparto.linee, key=lambda item: item.linea)
        ]
        return RepartoFiltriView(
            reparto_id=reparto.id,
            reparto=reparto.reparto,
            linee=linee,
        )


def load_filtri_by_sede(sede_id: int) -> SedeFiltriView | None:
    with get_session() as session:
        sede = session.scalar(
            select(Sede)
            .options(
                selectinload(Sede.reparti)
                .selectinload(Reparto.linee)
                .selectinload(Linea.quadri_elettrici)
                .selectinload(QuadroElettrico.filtri)
                .selectinload(Filtro.interventi)
            )
            .where(Sede.id == sede_id)
        )
        if sede is None:
            return None

        reparti = []
        for reparto in sorted(sede.reparti, key=lambda item: item.reparto):
            linee = [
                _linea_section(linea)
                for linea in sorted(reparto.linee, key=lambda item: item.linea)
            ]
            reparti.append(
                RepartoFiltriSection(
                    reparto_id=reparto.id,
                    reparto=reparto.reparto,
                    linee=linee,
                )
            )

        return SedeFiltriView(sede_id=sede.id, sede=sede.sede, reparti=reparti)


def load_filtri_by_linea(linea_id: int) -> LineaFiltriSection | None:
    with get_session() as session:
        linea = session.scalar(
            select(Linea)
            .options(
                selectinload(Linea.quadri_elettrici)
                .selectinload(QuadroElettrico.filtri)
                .selectinload(Filtro.interventi)
            )
            .where(Linea.id == linea_id)
        )
        if linea is None:
            return None
        return _linea_section(linea)


def load_filtri_by_quadro(quadro_id: int) -> list[FiltroCard]:
    with get_session() as session:
        quadro = session.scalar(
            select(QuadroElettrico)
            .options(
                selectinload(QuadroElettrico.filtri).selectinload(Filtro.interventi),
                selectinload(QuadroElettrico.linea).selectinload(Linea.reparto),
            )
            .where(QuadroElettrico.id == quadro_id)
        )
        if quadro is None:
            return []
        return _filtro_cards_from_quadri([quadro])


def load_quadro_detail(quadro_id: int) -> QuadroFiltroDetail | None:
    with get_session() as session:
        quadro = session.scalar(
            select(QuadroElettrico)
            .options(
                selectinload(QuadroElettrico.filtri).selectinload(Filtro.interventi),
                selectinload(QuadroElettrico.linea)
                .selectinload(Linea.reparto)
                .selectinload(Reparto.sede),
            )
            .where(QuadroElettrico.id == quadro_id)
        )
        if quadro is None:
            return None

        linea = quadro.linea
        reparto = linea.reparto
        sede = reparto.sede
        filtro = quadro.filtri[0] if quadro.filtri else None

        ultimo = _ultimo_intervento(filtro) if filtro else None
        frequenza = filtro.frequenza_intervento if filtro else None
        config = config_preavviso_per_filtro(filtro)
        stato = calcola_stato_filtro(ultimo, frequenza, config=config) if frequenza else "overdue"

        prossima_scadenza = None
        giorni_rimanenti = None
        giorni_preavviso = None
        data_inizio_preavviso = None
        if ultimo is not None and frequenza is not None:
            prossima_scadenza = calcola_scadenza_intervento(ultimo, frequenza)
            giorni_rimanenti = (prossima_scadenza - date.today()).days
            giorni_preavviso = calcola_giorni_preavviso(ultimo, prossima_scadenza, config=config)
            data_inizio_preavviso = prossima_scadenza - timedelta(days=giorni_preavviso)

        interventi = []
        if filtro is not None:
            interventi = [
                InterventoVoce(
                    intervento_id=intervento.id,
                    data=intervento.data,
                    note=intervento.note or "",
                )
                for intervento in sorted(filtro.interventi, key=lambda item: item.data, reverse=True)
            ]

        return QuadroFiltroDetail(
            quadro_elettrico_id=quadro.id,
            quadro_elettrico=quadro.quadro_elettrico,
            sede=sede.sede,
            reparto=reparto.reparto,
            linea=linea.linea,
            linea_id=linea.id,
            filtro_id=filtro.id if filtro else None,
            quantita_filtri=filtro.quantita_filtri if filtro else None,
            dimensione_filtri=filtro.dimensione_filtri if filtro else None,
            frequenza_intervento=frequenza,
            preavviso_descrizione=descrizione_preavviso_filtro(filtro),
            ultimo_intervento=ultimo,
            prossima_scadenza=prossima_scadenza,
            giorni_rimanenti=giorni_rimanenti,
            giorni_preavviso=giorni_preavviso,
            data_inizio_preavviso=data_inizio_preavviso,
            stato=stato,
            interventi=interventi,
        )


def load_report_summary(states: list[ReportFilterState] | None = None) -> ReportSummary:
    normalized_states = [state for state in (states or ["all"]) if state in {"all", "ok", "warning", "overdue"}]
    if not normalized_states or "all" in normalized_states:
        normalized_states = ["all"]
    else:
        normalized_states = [state for state in normalized_states if state != "all"]

    with get_session() as session:
        quadri = session.scalars(
            select(QuadroElettrico).options(
                selectinload(QuadroElettrico.filtri).selectinload(Filtro.interventi),
                selectinload(QuadroElettrico.linea)
                .selectinload(Linea.reparto)
                .selectinload(Reparto.sede),
            )
        ).all()

    quadri_scaduti_voci: list[ReportQuadroVoce] = []
    filtri_per_dimensione: dict[str, int] = {}
    quadri_ok = 0
    quadri_overdue = 0
    quadri_warning = 0

    for quadro in sorted(quadri, key=lambda item: item.quadro_elettrico):
        filtro = quadro.filtri[0] if quadro.filtri else None
        if filtro is None:
            continue

        ultimo = _ultimo_intervento(filtro)
        config = config_preavviso_per_filtro(filtro)
        stato = calcola_stato_filtro(ultimo, filtro.frequenza_intervento, config=config)
        if stato == "ok":
            quadri_ok += 1
        elif stato == "overdue":
            quadri_overdue += 1
        elif stato == "warning":
            quadri_warning += 1
        if normalized_states != ["all"] and stato not in normalized_states:
            continue

        filtri_per_dimensione[filtro.dimensione_filtri] = (
            filtri_per_dimensione.get(filtro.dimensione_filtri, 0) + filtro.quantita_filtri
        )

        prossima_scadenza = None
        giorni_scaduto = None
        giorni_rimanenti = None
        if ultimo is not None:
            prossima_scadenza = calcola_scadenza_intervento(ultimo, filtro.frequenza_intervento)
            giorni_scaduto = max(0, (date.today() - prossima_scadenza).days)
            giorni_rimanenti = max(0, (prossima_scadenza - date.today()).days)

        quadri_scaduti_voci.append(
            ReportQuadroVoce(
                quadro_elettrico_id=quadro.id,
                quadro_elettrico=quadro.quadro_elettrico,
                reparto=quadro.linea.reparto.reparto,
                linea=quadro.linea.linea,
                dimensione_filtri=filtro.dimensione_filtri,
                quantita_filtri=filtro.quantita_filtri,
                frequenza_intervento=filtro.frequenza_intervento,
                ultimo_intervento=ultimo,
                data_nuovo_intervento=prossima_scadenza,
                stato=stato,
                giorni_scaduto=giorni_scaduto,
                giorni_rimanenti=giorni_rimanenti,
            )
        )

    return ReportSummary(
        states=normalized_states,
        title=report_title(normalized_states),
        last_column_title="",
        quadri_scaduti=len(quadri_scaduti_voci),
        quadri_ok=quadri_ok,
        quadri_overdue=quadri_overdue,
        quadri_warning=quadri_warning,
        filtri_da_preparare=sum(filtri_per_dimensione.values()),
        filtri_per_dimensione=[
            ReportDimensioneVoce(dimensione_filtri=dimensione, quantita_filtri=quantita)
            for dimensione, quantita in sorted(filtri_per_dimensione.items())
        ],
        quadri_scaduti_voci=quadri_scaduti_voci,
    )


def load_home_status_summary() -> HomeStatusSummary:
    with get_session() as session:
        quadri = session.scalars(
            select(QuadroElettrico).options(
                selectinload(QuadroElettrico.filtri).selectinload(Filtro.interventi)
            )
        ).all()

    ok = 0
    warning = 0
    overdue = 0

    for quadro in quadri:
        filtro = quadro.filtri[0] if quadro.filtri else None
        if filtro is None:
            continue

        ultimo = _ultimo_intervento(filtro)
        config = config_preavviso_per_filtro(filtro)
        stato = calcola_stato_filtro(ultimo, filtro.frequenza_intervento, config=config)

        if stato == "ok":
            ok += 1
        elif stato == "warning":
            warning += 1
        else:
            overdue += 1

    return HomeStatusSummary(ok=ok, warning=warning, overdue=overdue)
