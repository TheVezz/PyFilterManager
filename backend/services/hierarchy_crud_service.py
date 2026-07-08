"""Operazioni CRUD e spostamento sulla gerarchia impianto."""

from typing import cast

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.database.db_manager import get_session
from backend.models import (
    Filtro,
    Intervento,
    Linea,
    QuadroElettrico,
    Reparto,
    Sede,
)
from backend.schemas.hierarchy import (
    CHILD_NODE_TYPES,
    ChildCreate,
    EntityMove,
    EntityRename,
    NodeType,
    PreavvisoFiltroInput,
    QuadroFiltroCreate,
    QuadroFiltroEditData,
    QuadroFiltroUpdate,
    SedeCreate,
)

NODE_MODELS = {
    "sede": Sede,
    "reparto": Reparto,
    "linea": Linea,
    "quadro_elettrico": QuadroElettrico,
}

NAME_FIELDS = {
    "sede": "sede",
    "reparto": "reparto",
    "linea": "linea",
    "quadro_elettrico": "quadro_elettrico",
}

PARENT_FIELDS = {
    "reparto": "sede_id",
    "linea": "reparto_id",
    "quadro_elettrico": "linea_id",
}


class HierarchyCrudError(Exception):
    pass


def _apply_preavviso_filtro(filtro: Filtro, data: PreavvisoFiltroInput) -> None:
    filtro.preavviso_usa_globale = data.preavviso_usa_globale
    if data.preavviso_usa_globale:
        filtro.preavviso_percentuale = None
        filtro.preavviso_massimo_giorni = None
        return

    filtro.preavviso_percentuale = data.preavviso_percentuale
    filtro.preavviso_massimo_giorni = data.preavviso_massimo_giorni


def get_quadro_linea_id(quadro_id: int) -> int:
    with get_session() as session:
        quadro = session.get(QuadroElettrico, quadro_id)
        if quadro is None:
            raise HierarchyCrudError("Quadro elettrico non trovato.")
        return quadro.linea_id


def _quadro_name_taken(
    session,
    linea_id: int,
    name: str,
    exclude_id: int | None = None,
) -> bool:
    stmt = select(QuadroElettrico.id).where(
        QuadroElettrico.linea_id == linea_id,
        func.lower(QuadroElettrico.quadro_elettrico) == name.strip().lower(),
    )
    if exclude_id is not None:
        stmt = stmt.where(QuadroElettrico.id != exclude_id)
    return session.scalar(stmt.limit(1)) is not None


def check_quadro_name_available(
    linea_id: int,
    name: str,
    exclude_id: int | None = None,
) -> str | None:
    with get_session() as session:
        if _quadro_name_taken(session, linea_id, name, exclude_id):
            return "Un quadro elettrico con questo nome esiste già in questa linea."
    return None


def create_sede(data: SedeCreate) -> int:
    with get_session() as session:
        sede = Sede(sede=data.sede)
        session.add(sede)
        session.commit()
        return sede.id


def create_child(data: ChildCreate) -> int:
    child_type = CHILD_NODE_TYPES.get(data.parent_type)
    if child_type is None:
        raise HierarchyCrudError(
            f"Non è possibile creare un figlio per '{data.parent_type}'."
        )

    parent_model = NODE_MODELS[data.parent_type]
    child_model = NODE_MODELS[child_type]
    parent_field = PARENT_FIELDS[child_type]
    name_field = NAME_FIELDS[child_type]

    with get_session() as session:
        parent = session.get(parent_model, data.parent_id)
        if parent is None:
            raise HierarchyCrudError("Elemento padre non trovato.")

        child = child_model(**{parent_field: data.parent_id, name_field: data.name})
        session.add(child)
        session.commit()
        return cast(int, getattr(child, "id"))


def create_quadro_with_filtro(data: QuadroFiltroCreate) -> int:
    with get_session() as session:
        linea = session.get(Linea, data.linea_id)
        if linea is None:
            raise HierarchyCrudError("Linea non trovata.")

        if _quadro_name_taken(session, data.linea_id, data.quadro_elettrico):
            raise HierarchyCrudError(
                "Un quadro elettrico con questo nome esiste già in questa linea."
            )

        quadro = QuadroElettrico(
            linea_id=data.linea_id,
            quadro_elettrico=data.quadro_elettrico,
        )
        session.add(quadro)
        session.flush()

        filtro = Filtro(
            quadro_elettrico_id=quadro.id,
            quantita_filtri=data.quantita_filtri,
            dimensione_filtri=data.dimensione_filtri,
            frequenza_intervento=data.frequenza_intervento,
        )
        _apply_preavviso_filtro(filtro, data)
        session.add(filtro)
        session.flush()

        intervento = Intervento(
            filtro_id=filtro.id,
            data=data.data_primo_intervento,
        )
        session.add(intervento)
        session.commit()
        return quadro.id


def load_quadro_filtro_edit(quadro_id: int) -> QuadroFiltroEditData:
    with get_session() as session:
        quadro = session.scalar(
            select(QuadroElettrico)
            .options(selectinload(QuadroElettrico.filtri))
            .where(QuadroElettrico.id == quadro_id)
        )
        if quadro is None:
            raise HierarchyCrudError("Quadro elettrico non trovato.")

        filtro = quadro.filtri[0] if quadro.filtri else None
        usa_globale = filtro.preavviso_usa_globale if filtro else True

        return QuadroFiltroEditData(
            quadro_elettrico_id=quadro.id,
            linea_id=quadro.linea_id,
            quadro_elettrico=quadro.quadro_elettrico,
            filtro_id=filtro.id if filtro else None,
            quantita_filtri=filtro.quantita_filtri if filtro else 1,
            dimensione_filtri=filtro.dimensione_filtri if filtro else "",
            frequenza_intervento=filtro.frequenza_intervento if filtro else "",
            preavviso_usa_globale=usa_globale,
            preavviso_percentuale=(
                filtro.preavviso_percentuale if filtro and not usa_globale else None
            ),
            preavviso_massimo_giorni=(
                filtro.preavviso_massimo_giorni if filtro and not usa_globale else None
            ),
        )


def update_quadro_with_filtro(data: QuadroFiltroUpdate) -> None:
    with get_session() as session:
        quadro = session.scalar(
            select(QuadroElettrico)
            .options(selectinload(QuadroElettrico.filtri))
            .where(QuadroElettrico.id == data.quadro_elettrico_id)
        )
        if quadro is None:
            raise HierarchyCrudError("Quadro elettrico non trovato.")

        if _quadro_name_taken(
            session,
            quadro.linea_id,
            data.quadro_elettrico,
            exclude_id=data.quadro_elettrico_id,
        ):
            raise HierarchyCrudError(
                "Un quadro elettrico con questo nome esiste già in questa linea."
            )

        quadro.quadro_elettrico = data.quadro_elettrico

        filtro = quadro.filtri[0] if quadro.filtri else None
        if filtro is None:
            filtro = Filtro(
                quadro_elettrico_id=quadro.id,
                quantita_filtri=data.quantita_filtri,
                dimensione_filtri=data.dimensione_filtri,
                frequenza_intervento=data.frequenza_intervento,
            )
            _apply_preavviso_filtro(filtro, data)
            session.add(filtro)
        else:
            filtro.quantita_filtri = data.quantita_filtri
            filtro.dimensione_filtri = data.dimensione_filtri
            filtro.frequenza_intervento = data.frequenza_intervento
            _apply_preavviso_filtro(filtro, data)

        session.commit()


def update_entity(data: EntityRename) -> None:
    model = NODE_MODELS.get(data.node_type)
    name_field = NAME_FIELDS.get(data.node_type)
    if model is None or name_field is None:
        raise HierarchyCrudError(f"Tipo '{data.node_type}' non supportato.")

    with get_session() as session:
        entity = session.get(model, data.entity_id)
        if entity is None:
            raise HierarchyCrudError("Elemento non trovato.")

        if data.node_type == "quadro_elettrico":
            quadro = cast(QuadroElettrico, entity)
            if _quadro_name_taken(
                session,
                quadro.linea_id,
                data.name,
                exclude_id=data.entity_id,
            ):
                raise HierarchyCrudError(
                    "Un quadro elettrico con questo nome esiste già in questa linea."
                )

        setattr(entity, name_field, data.name)
        session.commit()


def delete_entity(node_type: str, entity_id: int) -> None:
    model = NODE_MODELS.get(node_type)
    if model is None:
        raise HierarchyCrudError(f"Tipo '{node_type}' non supportato.")

    with get_session() as session:
        entity = session.get(model, entity_id)
        if entity is None:
            raise HierarchyCrudError("Elemento non trovato.")
        session.delete(entity)
        session.commit()


def move_entity(data: EntityMove) -> None:
    parent_field = PARENT_FIELDS.get(data.node_type)
    if parent_field is None:
        raise HierarchyCrudError(f"Non è possibile spostare '{data.node_type}'.")

    with get_session() as session:
        entity = session.get(NODE_MODELS[data.node_type], data.entity_id)
        if entity is None:
            raise HierarchyCrudError("Elemento non trovato.")

        if data.node_type == "quadro_elettrico":
            quadro = cast(QuadroElettrico, entity)
            if _quadro_name_taken(
                session,
                data.new_parent_id,
                quadro.quadro_elettrico,
                exclude_id=data.entity_id,
            ):
                raise HierarchyCrudError(
                    "Un quadro elettrico con questo nome esiste già nella linea "
                    "di destinazione."
                )

        setattr(entity, parent_field, data.new_parent_id)
        session.commit()


def list_move_targets(node_type: str, entity_id: int) -> list[tuple[int, str]]:
    with get_session() as session:
        if node_type == "reparto":
            reparto = session.get(Reparto, entity_id)
            if reparto is None:
                raise HierarchyCrudError("Reparto non trovato.")
            sedi = session.scalars(select(Sede).order_by(Sede.sede)).all()
            return [(sede.id, sede.sede) for sede in sedi if sede.id != reparto.sede_id]

        if node_type == "linea":
            linea = session.get(Linea, entity_id)
            if linea is None:
                raise HierarchyCrudError("Linea non trovata.")
            reparti = session.scalars(
                select(Reparto)
                .options(selectinload(Reparto.sede))
                .order_by(Reparto.reparto)
            ).all()
            return [
                (reparto.id, f"{reparto.sede.sede} / {reparto.reparto}")
                for reparto in reparti
                if reparto.id != linea.reparto_id
            ]

        if node_type == "quadro_elettrico":
            quadro = session.get(QuadroElettrico, entity_id)
            if quadro is None:
                raise HierarchyCrudError("Quadro elettrico non trovato.")
            linee = session.scalars(
                select(Linea)
                .options(selectinload(Linea.reparto).selectinload(Reparto.sede))
                .order_by(Linea.linea)
            ).all()
            return [
                (
                    linea.id,
                    (
                        f"{linea.reparto.sede.sede} / "
                        f"{linea.reparto.reparto} / {linea.linea}"
                    ),
                )
                for linea in linee
                if linea.id != quadro.linea_id
            ]

    raise HierarchyCrudError(f"Non è possibile spostare '{node_type}'.")


def validate_child_create(parent_type: str, parent_id: int, name: str) -> ChildCreate:
    if parent_type not in CHILD_NODE_TYPES:
        raise HierarchyCrudError("Dati non validi.")
    try:
        return ChildCreate(
            parent_type=cast(NodeType, parent_type),
            parent_id=parent_id,
            name=name,
        )
    except ValidationError as error:
        raise HierarchyCrudError("Dati non validi.") from error


def validate_sede_create(name: str) -> SedeCreate:
    try:
        return SedeCreate(sede=name)
    except ValidationError as error:
        raise HierarchyCrudError("Dati non validi.") from error


def validate_entity_rename(node_type: str, entity_id: int, name: str) -> EntityRename:
    if node_type not in NODE_MODELS:
        raise HierarchyCrudError("Dati non validi.")
    try:
        return EntityRename(
            node_type=cast(NodeType, node_type),
            entity_id=entity_id,
            name=name,
        )
    except ValidationError as error:
        raise HierarchyCrudError("Dati non validi.") from error


def validate_entity_move(
    node_type: str,
    entity_id: int,
    new_parent_id: int,
) -> EntityMove:
    if node_type not in PARENT_FIELDS:
        raise HierarchyCrudError("Dati non validi.")
    try:
        return EntityMove(
            node_type=cast(NodeType, node_type),
            entity_id=entity_id,
            new_parent_id=new_parent_id,
        )
    except ValidationError as error:
        raise HierarchyCrudError("Dati non validi.") from error
