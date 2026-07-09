from backend.models.base import Base
from backend.models.filtro import Filtro
from backend.models.impianto import Impianto
from backend.models.intervento import Intervento
from backend.models.quadro_elettrico import QuadroElettrico
from backend.models.reparto import Reparto
from backend.models.sede import Sede

__all__ = [
    "Base",
    "Sede",
    "Reparto",
    "Impianto",
    "QuadroElettrico",
    "Filtro",
    "Intervento",
]
