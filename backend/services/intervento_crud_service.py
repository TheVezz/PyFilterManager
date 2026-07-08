"""Operazioni CRUD sugli interventi filtro."""

from pydantic import ValidationError

from backend.database.db_manager import get_session
from backend.models import Filtro, Intervento
from backend.schemas.filtri import InterventoCreate, InterventoUpdate


class InterventoCrudError(Exception):
    pass


def validate_intervento_create(data: InterventoCreate) -> InterventoCreate:
    try:
        return InterventoCreate.model_validate(data)
    except ValidationError as error:
        raise InterventoCrudError("Controlla i dati inseriti.") from error


def validate_intervento_update(data: InterventoUpdate) -> InterventoUpdate:
    try:
        return InterventoUpdate.model_validate(data)
    except ValidationError as error:
        raise InterventoCrudError("Controlla i dati inseriti.") from error


def create_intervento(data: InterventoCreate) -> int:
    with get_session() as session:
        filtro = session.get(Filtro, data.filtro_id)
        if filtro is None:
            raise InterventoCrudError("Filtro non trovato.")

        intervento = Intervento(
            filtro_id=data.filtro_id,
            data=data.data,
            note=data.note,
        )
        session.add(intervento)
        session.commit()
        session.refresh(intervento)
        return intervento.id


def update_intervento(data: InterventoUpdate) -> None:
    with get_session() as session:
        intervento = session.get(Intervento, data.intervento_id)
        if intervento is None:
            raise InterventoCrudError("Intervento non trovato.")

        intervento.data = data.data
        intervento.note = data.note
        session.commit()


def delete_intervento(intervento_id: int) -> None:
    with get_session() as session:
        intervento = session.get(Intervento, intervento_id)
        if intervento is None:
            raise InterventoCrudError("Intervento non trovato.")

        session.delete(intervento)
        session.commit()
