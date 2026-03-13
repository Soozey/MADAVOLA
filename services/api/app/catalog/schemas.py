from datetime import datetime

from pydantic import BaseModel


class ProductCatalogCreate(BaseModel):
    code: str
    nom: str
    famille: str = "PIERRE"
    filiere: str = "PIERRE"
    sous_filiere: str
    allowed_units: list[str]
    required_attributes: list[str]
    export_restricted: bool = False
    export_rules: dict = {}


class ProductCatalogUpdate(BaseModel):
    nom: str | None = None
    sous_filiere: str | None = None
    allowed_units: list[str] | None = None
    required_attributes: list[str] | None = None
    export_restricted: bool | None = None
    export_rules: dict | None = None
    status: str | None = None


class ProductCatalogOut(BaseModel):
    id: int
    code: str
    nom: str
    famille: str
    filiere: str
    sous_filiere: str
    allowed_units: list[str]
    required_attributes: list[str]
    export_restricted: bool
    export_rules: dict
    status: str
    created_at: datetime
