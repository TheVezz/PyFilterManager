from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.intervento import Intervento
    from backend.models.quadro_elettrico import QuadroElettrico


class Filtro(Base):
    __tablename__ = "filtri"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quantita_filtri: Mapped[int] = mapped_column(Integer, nullable=False)
    dimensione_filtri: Mapped[str] = mapped_column(String, nullable=False)
    frequenza_intervento: Mapped[str] = mapped_column(String, nullable=False)
    preavviso_usa_globale: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
    preavviso_percentuale: Mapped[float | None] = mapped_column(Float, nullable=True)
    preavviso_massimo_giorni: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quadro_elettrico_id: Mapped[int] = mapped_column(
        ForeignKey("quadro_elettrico.id"),
        nullable=False,
    )

    quadro_elettrico: Mapped["QuadroElettrico"] = relationship(back_populates="filtri")
    interventi: Mapped[list["Intervento"]] = relationship(
        back_populates="filtro",
        cascade="all, delete-orphan",
    )
