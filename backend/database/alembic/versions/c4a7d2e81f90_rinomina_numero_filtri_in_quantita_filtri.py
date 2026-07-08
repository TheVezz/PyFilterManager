"""rinomina numero_filtri in quantita_filtri

Revision ID: c4a7d2e81f90
Revises: b8e4f1a92c3d
Create Date: 2026-07-08 01:10:00.000000

"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4a7d2e81f90"
down_revision: Union[str, Sequence[str], None] = "b8e4f1a92c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parse_quantita(value: str) -> int:
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
    if "quantita_filtri" in columns and "numero_filtri" not in columns:
        return

    bind = op.get_bind()

    if "numero_filtri" not in columns:
        op.add_column(
            "filtri",
            sa.Column("quantita_filtri", sa.Integer(), nullable=False, server_default="1"),
        )
        return

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

    rows = bind.execute(
        sa.text(
            """
            SELECT id, numero_filtri, dimensione_filtri, frequenza_intervento, quadro_elettrico_id
            FROM filtri
            """
        )
    ).fetchall()

    for row_id, old_value, dimensione, frequenza, quadro_id in rows:
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
                "quantita": _parse_quantita(old_value),
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
    if "quantita_filtri" not in columns:
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
