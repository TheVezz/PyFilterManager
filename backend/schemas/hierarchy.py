from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.schemas.frequenza import normalize_frequenza_intervento

NodeType = Literal["sede", "reparto", "linea", "quadro_elettrico"]

CHILD_NODE_TYPES: dict[NodeType, NodeType] = {
    "sede": "reparto",
    "reparto": "linea",
    "linea": "quadro_elettrico",
}

MOVABLE_NODE_TYPES: set[NodeType] = {"reparto", "linea", "quadro_elettrico"}

DIMENSIONE_FILTRI_PATTERN = r"^\d+x\d+$"


class AppSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class PreavvisoFiltroInput(AppSchema):
    preavviso_usa_globale: bool = True
    preavviso_percentuale: float | None = Field(default=None, ge=0, le=100)
    preavviso_massimo_giorni: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_preavviso_personalizzato(self) -> "PreavvisoFiltroInput":
        if self.preavviso_usa_globale:
            return self
        if self.preavviso_percentuale is None:
            raise ValueError("Inserisci la percentuale per l'in scadenza.")
        if self.preavviso_massimo_giorni is None:
            raise ValueError("Inserisci il tetto massimo in giorni per l'in scadenza.")
        return self


class TreeNode(AppSchema):
    label: str = Field(min_length=1)
    node_type: NodeType
    entity_id: int = Field(gt=0)
    children: list["TreeNode"] = Field(default_factory=list)


class NameInput(AppSchema):
    name: str = Field(min_length=1)


class SedeCreate(AppSchema):
    sede: str = Field(min_length=1)


class ChildCreate(AppSchema):
    parent_type: NodeType
    parent_id: int = Field(gt=0)
    name: str = Field(min_length=1)


class EntityRename(AppSchema):
    node_type: NodeType
    entity_id: int = Field(gt=0)
    name: str = Field(min_length=1)


class EntityDelete(AppSchema):
    node_type: NodeType
    entity_id: int = Field(gt=0)


class EntityMove(AppSchema):
    node_type: NodeType
    entity_id: int = Field(gt=0)
    new_parent_id: int = Field(gt=0)


class QuadroFiltroCreate(PreavvisoFiltroInput):
    linea_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    quantita_filtri: int = Field(gt=0)
    dimensione_filtri: str = Field(
        min_length=1,
        pattern=DIMENSIONE_FILTRI_PATTERN,
        description="Formato larghezza x altezza, es. 600x600",
    )
    data_primo_intervento: date
    frequenza_intervento: str = Field(min_length=1)

    @field_validator("frequenza_intervento")
    @classmethod
    def validate_frequenza_intervento(cls, value: str) -> str:
        return normalize_frequenza_intervento(value)


class QuadroFiltroUpdate(PreavvisoFiltroInput):
    quadro_elettrico_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    quantita_filtri: int = Field(gt=0)
    dimensione_filtri: str = Field(
        min_length=1,
        pattern=DIMENSIONE_FILTRI_PATTERN,
        description="Formato larghezza x altezza, es. 600x600",
    )
    frequenza_intervento: str = Field(min_length=1)

    @field_validator("frequenza_intervento")
    @classmethod
    def validate_frequenza_intervento(cls, value: str) -> str:
        return normalize_frequenza_intervento(value)


class QuadroFiltroEditData(AppSchema):
    quadro_elettrico_id: int = Field(gt=0)
    linea_id: int = Field(gt=0)
    quadro_elettrico: str = Field(min_length=1)
    filtro_id: int | None = None
    quantita_filtri: int = Field(default=1, gt=0)
    dimensione_filtri: str = ""
    frequenza_intervento: str = ""
    preavviso_usa_globale: bool = True
    preavviso_percentuale: float | None = None
    preavviso_massimo_giorni: int | None = None


class FiltroCreate(AppSchema):
    quadro_elettrico_id: int = Field(gt=0)
    quantita_filtri: int = Field(gt=0)
    dimensione_filtri: str = Field(
        min_length=1,
        pattern=DIMENSIONE_FILTRI_PATTERN,
        description="Formato larghezza x altezza, es. 600x600",
    )
    frequenza_intervento: str = Field(min_length=1)

    @field_validator("frequenza_intervento")
    @classmethod
    def validate_frequenza_intervento(cls, value: str) -> str:
        return normalize_frequenza_intervento(value)
