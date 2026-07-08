from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.filtro import Filtro


class Intervento(Base):
    __tablename__ = "interventi"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    filtro_id: Mapped[int] = mapped_column(ForeignKey("filtri.id"), nullable=False)

    filtro: Mapped["Filtro"] = relationship(back_populates="interventi")
