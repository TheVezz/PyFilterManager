from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.db_manager import get_session
from backend.models import Linea, QuadroElettrico, Reparto, Sede
from backend.schemas.hierarchy import TreeNode


def load_hierarchy() -> list[TreeNode]:
    with get_session() as session:
        sedi = session.scalars(
            select(Sede)
            .options(
                selectinload(Sede.reparti)
                .selectinload(Reparto.linee)
                .selectinload(Linea.quadri_elettrici)
            )
            .order_by(Sede.sede)
        ).all()

    return [_sede_node(sede) for sede in sedi]


def _sede_node(sede: Sede) -> TreeNode:
    return TreeNode(
        label=sede.sede,
        node_type="sede",
        entity_id=sede.id,
        children=[
            _reparto_node(reparto)
            for reparto in sorted(sede.reparti, key=lambda reparto_item: reparto_item.reparto)
        ],
    )


def _reparto_node(reparto: Reparto) -> TreeNode:
    return TreeNode(
        label=reparto.reparto,
        node_type="reparto",
        entity_id=reparto.id,
        children=[
            _linea_node(linea)
            for linea in sorted(reparto.linee, key=lambda linea_item: linea_item.linea)
        ],
    )


def _linea_node(linea: Linea) -> TreeNode:
    return TreeNode(
        label=linea.linea,
        node_type="linea",
        entity_id=linea.id,
        children=[
            _quadro_node(quadro)
            for quadro in sorted(linea.quadri_elettrici, key=lambda q: q.quadro_elettrico)
        ],
    )


def _quadro_node(quadro: QuadroElettrico) -> TreeNode:
    return TreeNode(
        label=quadro.quadro_elettrico,
        node_type="quadro_elettrico",
        entity_id=quadro.id,
    )
