from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.quadro_elettrico import QuadroElettrico
    from backend.models.reparto import Reparto


class Linea(Base):
    __tablename__ = "linea"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    linea: Mapped[str] = mapped_column(String, nullable=False)
    reparto_id: Mapped[int] = mapped_column(ForeignKey("reparto.id"), nullable=False)

    reparto: Mapped["Reparto"] = relationship(back_populates="linee")
    quadri_elettrici: Mapped[list["QuadroElettrico"]] = relationship(
        back_populates="linea",
        cascade="all, delete-orphan",
    )
