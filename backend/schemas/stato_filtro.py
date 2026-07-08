import sys
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from backend.schemas.settings import PYPROJECT_PATH

FiltroStato = Literal["ok", "warning", "overdue"]


class StatoFiltroConfig(BaseModel):
    """Parametri per il calcolo dello stato filtro (da pyproject.toml)."""

    preavviso_percentuale: float = Field(default=15.0, ge=0, le=100)
    preavviso_massimo_giorni: int = Field(default=14, ge=1)


def _load_toml() -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


@lru_cache
def get_stato_filtro_config() -> StatoFiltroConfig:
    data = _load_toml()
    stato = data.get("tool", {}).get("filtri", {}).get("stato", {})
    return StatoFiltroConfig.model_validate(stato)
