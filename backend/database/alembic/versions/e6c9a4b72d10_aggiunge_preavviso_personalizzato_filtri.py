"""aggiunge preavviso personalizzato a filtri

Revision ID: e6c9a4b72d10
Revises: d5b8c3f04a21
Create Date: 2026-07-08 01:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e6c9a4b72d10"
down_revision: Union[str, Sequence[str], None] = "d5b8c3f04a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _column_names("filtri")
    if "preavviso_usa_globale" in columns:
        return

    op.add_column(
        "filtri",
        sa.Column(
            "preavviso_usa_globale",
            sa.Boolean(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column("filtri", sa.Column("preavviso_percentuale", sa.Float(), nullable=True))
    op.add_column("filtri", sa.Column("preavviso_massimo_giorni", sa.Integer(), nullable=True))


def downgrade() -> None:
    columns = _column_names("filtri")
    if "preavviso_usa_globale" not in columns:
        return

    op.drop_column("filtri", "preavviso_massimo_giorni")
    op.drop_column("filtri", "preavviso_percentuale")
    op.drop_column("filtri", "preavviso_usa_globale")
