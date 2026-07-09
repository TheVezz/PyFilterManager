from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.filtro import Filtro
    from backend.models.impianto import Impianto


class QuadroElettrico(Base):
    __tablename__ = "quadro_elettrico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quadro_elettrico: Mapped[str] = mapped_column(String, nullable=False)
    impianto_id: Mapped[int] = mapped_column(ForeignKey("impianto.id"), nullable=False)

    impianto: Mapped["Impianto"] = relationship(back_populates="quadri_elettrici")
    filtri: Mapped[list["Filtro"]] = relationship(
        back_populates="quadro_elettrico",
        cascade="all, delete-orphan",
    )
