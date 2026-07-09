"""Popolamento del database con dati di esempio."""

from sqlalchemy import delete

from backend.database.db_manager import get_session
from backend.database.init_database import init_database
from backend.factories import (
    ImpiantoFactory,
    QuadroElettricoFactory,
    RepartoFactory,
    SedeFactory,
    bind_factory_session,
    crea_quadro_con_filtro,
)
from backend.models import Filtro, Impianto, Intervento, QuadroElettrico, Reparto, Sede


def seed_dev_data(*, clear: bool = False) -> None:
    init_database()

    with get_session() as session:
        bind_factory_session(session)

        if clear:
            session.execute(delete(Intervento))
            session.execute(delete(Filtro))
            session.execute(delete(QuadroElettrico))
            session.execute(delete(Impianto))
            session.execute(delete(Reparto))
            session.execute(delete(Sede))
            session.commit()

        sede = SedeFactory(sede="Stabilimento Milano")
        reparto_prod = RepartoFactory(sede=sede, reparto="Produzione")
        reparto_uffici = RepartoFactory(sede=sede, reparto="Uffici")

        impianto_1 = ImpiantoFactory(reparto=reparto_prod, impianto="Impianto 1")
        impianto_2 = ImpiantoFactory(reparto=reparto_prod, impianto="Impianto 2")
        impianto_uffici = ImpiantoFactory(reparto=reparto_uffici, impianto="Climatizzazione")

        # Un quadro per ogni caso di stato (badge ✓ ! ✗)
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-OK",
            quantita_filtri=4,
            dimensione_filtri="600x600",
            frequenza_intervento="12 mesi",
            stato="ok",
        )
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-WARN",
            quantita_filtri=6,
            dimensione_filtri="800x800",
            frequenza_intervento="30 giorni",
            stato="warning",
        )
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-OVER",
            quantita_filtri=8,
            dimensione_filtri="1000x1000",
            frequenza_intervento="6 mesi",
            stato="overdue",
        )
        QuadroElettricoFactory(
            impianto=impianto_1,
            quadro_elettrico="QED-NOINT",
            quantita_filtri=2,
            dimensione_filtri="500x500",
            frequenza_intervento="12 mesi",
            stato=None,
        )

        # Un quadro per ogni tipo di frequenza
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-GIORNI",
            quantita_filtri=3,
            dimensione_filtri="600x600",
            frequenza_intervento="30 giorni",
            stato="ok",
        )
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-SETT",
            quantita_filtri=5,
            dimensione_filtri="600x600",
            frequenza_intervento="2 settimane",
            stato="ok",
        )
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-TRIM",
            quantita_filtri=7,
            dimensione_filtri="600x600",
            frequenza_intervento="trimestrale",
            stato="ok",
        )
        crea_quadro_con_filtro(
            impianto=impianto_1,
            quadro_elettrico="QED-ANN",
            quantita_filtri=12,
            dimensione_filtri="600x600",
            frequenza_intervento="annuale",
            stato="ok",
            storico_interventi=2,
        )

        crea_quadro_con_filtro(
            impianto=impianto_2,
            quadro_elettrico="QED-02",
            quantita_filtri=3,
            dimensione_filtri="1000x1000",
            frequenza_intervento="semestrale",
            stato="warning",
        )
        crea_quadro_con_filtro(
            impianto=impianto_uffici,
            quadro_elettrico="QED-U1",
            quantita_filtri=4,
            dimensione_filtri="500x500",
            frequenza_intervento="bimestrale",
            stato="ok",
        )

        session.commit()
