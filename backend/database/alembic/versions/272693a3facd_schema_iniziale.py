"""schema iniziale

Revision ID: 272693a3facd
Revises:
Create Date: 2026-07-07 15:02:21.760058

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "272693a3facd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sede",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sede", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reparto",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reparto", sa.String(), nullable=False),
        sa.Column("sede_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sede_id"], ["sede.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "linea",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("linea", sa.String(), nullable=False),
        sa.Column("reparto_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["reparto_id"], ["reparto.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quadro_elettrico",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quadro_elettrico", sa.String(), nullable=False),
        sa.Column("linea_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["linea_id"], ["linea.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "filtri",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero_filtri", sa.String(), nullable=False),
        sa.Column("dimensione_filtri", sa.String(), nullable=False),
        sa.Column("quadro_elettrico_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["quadro_elettrico_id"], ["quadro_elettrico.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "interventi",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("filtro_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["filtro_id"], ["filtri.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("interventi")
    op.drop_table("filtri")
    op.drop_table("quadro_elettrico")
    op.drop_table("linea")
    op.drop_table("reparto")
    op.drop_table("sede")
