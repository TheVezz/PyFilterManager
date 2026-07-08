"""aggiunge frequenza_intervento a filtri

Revision ID: b8e4f1a92c3d
Revises: 272693a3facd
Create Date: 2026-07-07 23:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8e4f1a92c3d"
down_revision: Union[str, Sequence[str], None] = "272693a3facd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("filtri")}
    if "frequenza_intervento" in columns:
        return

    op.add_column(
        "filtri",
        sa.Column(
            "frequenza_intervento",
            sa.String(),
            nullable=False,
            server_default="12 mesi",
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("filtri")}
    if "frequenza_intervento" not in columns:
        return

    op.drop_column("filtri", "frequenza_intervento")
