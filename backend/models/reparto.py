from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.impianto import Impianto
    from backend.models.sede import Sede


class Reparto(Base):
    __tablename__ = "reparto"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reparto: Mapped[str] = mapped_column(String, nullable=False)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sede.id"), nullable=False)

    sede: Mapped["Sede"] = relationship(back_populates="reparti")
    impianti: Mapped[list["Impianto"]] = relationship(
        back_populates="reparto",
        cascade="all, delete-orphan",
    )
