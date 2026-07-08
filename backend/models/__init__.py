from backend.models.base import Base
from backend.models.filtro import Filtro
from backend.models.intervento import Intervento
from backend.models.linea import Linea
from backend.models.quadro_elettrico import QuadroElettrico
from backend.models.reparto import Reparto
from backend.models.sede import Sede

__all__ = [
    "Base",
    "Sede",
    "Reparto",
    "Linea",
    "QuadroElettrico",
    "Filtro",
    "Intervento",
]
