"""completa rinomina quantita_filtri se rimasta parziale

Revision ID: d5b8c3f04a21
Revises: c4a7d2e81f90
Create Date: 2026-07-08 01:15:00.000000

"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5b8c3f04a21"
down_revision: Union[str, Sequence[str], None] = "c4a7d2e81f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parse_quantita(value: str | int | None) -> int:
    if isinstance(value, int):
        return max(1, value)

    text = (value or "").strip()
    if text.isdigit():
        return max(1, int(text))

    matches = re.findall(r"\d+", text)
    if matches:
        return max(1, int(matches[-1]))

    return 1


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _column_names("filtri")
    if "numero_filtri" not in columns:
        return

    bind = op.get_bind()
    has_quantita = "quantita_filtri" in columns

    bind.execute(
        sa.text(
            """
            CREATE TABLE filtri_new (
                id INTEGER NOT NULL,
                quantita_filtri INTEGER NOT NULL,
                dimensione_filtri VARCHAR NOT NULL,
                frequenza_intervento VARCHAR NOT NULL DEFAULT '12 mesi',
                quadro_elettrico_id INTEGER NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(quadro_elettrico_id) REFERENCES quadro_elettrico (id)
            )
            """
        )
    )

    select_sql = (
        """
        SELECT id, quantita_filtri, numero_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
        FROM filtri
        """
        if has_quantita
        else """
        SELECT id, numero_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
        FROM filtri
        """
    )

    rows = bind.execute(sa.text(select_sql)).fetchall()

    for row in rows:
        if has_quantita:
            row_id, quantita, old_value, dimensione, frequenza, quadro_id = row
            value = quantita if quantita is not None else _parse_quantita(old_value)
        else:
            row_id, old_value, dimensione, frequenza, quadro_id = row
            value = _parse_quantita(old_value)

        bind.execute(
            sa.text(
                """
                INSERT INTO filtri_new (
                    id, quantita_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
                ) VALUES (:id, :quantita, :dimensione, :frequenza, :quadro_id)
                """
            ),
            {
                "id": row_id,
                "quantita": value,
                "dimensione": dimensione,
                "frequenza": frequenza,
                "quadro_id": quadro_id,
            },
        )

    bind.execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_filtri"))
    op.drop_table("filtri")
    op.rename_table("filtri_new", "filtri")


def downgrade() -> None:
    columns = _column_names("filtri")
    if "numero_filtri" in columns or "quantita_filtri" not in columns:
        return

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            CREATE TABLE filtri_new (
                id INTEGER NOT NULL,
                numero_filtri VARCHAR NOT NULL,
                dimensione_filtri VARCHAR NOT NULL,
                frequenza_intervento VARCHAR NOT NULL DEFAULT '12 mesi',
                quadro_elettrico_id INTEGER NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(quadro_elettrico_id) REFERENCES quadro_elettrico (id)
            )
            """
        )
    )

    rows = bind.execute(
        sa.text(
            """
            SELECT id, quantita_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
            FROM filtri
            """
        )
    ).fetchall()

    for row_id, quantita, dimensione, frequenza, quadro_id in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO filtri_new (
                    id, numero_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
                ) VALUES (:id, :numero, :dimensione, :frequenza, :quadro_id)
                """
            ),
            {
                "id": row_id,
                "numero": str(quantita),
                "dimensione": dimensione,
                "frequenza": frequenza,
                "quadro_id": quadro_id,
            },
        )

    op.drop_table("filtri")
    op.rename_table("filtri_new", "filtri")
