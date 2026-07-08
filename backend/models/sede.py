from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.reparto import Reparto


class Sede(Base):
    __tablename__ = "sede"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sede: Mapped[str] = mapped_column(String, nullable=False)

    reparti: Mapped[list["Reparto"]] = relationship(
        back_populates="sede",
        cascade="all, delete-orphan",
    )
