from datetime import date

from pydantic import BaseModel


class AlerteItem(BaseModel):
    id: str
    type: str
    libelle: str
    severite: str
    created_at: str


class DashboardNationalOut(BaseModel):
    volume_created: float
    transactions_total: float
    nb_acteurs: int
    nb_lots: int
    nb_exports_en_attente: int = 0
    alertes_strategiques: list[AlerteItem]


class DashboardRegionalOut(BaseModel):
    region_id: int
    region_code: str
    region_name: str
    volume_created: float
    transactions_total: float
    nb_acteurs: int
    nb_lots: int


class DashboardCommuneOut(BaseModel):
    commune_id: int
    commune_code: str
    commune_name: str
    volume_created: float
    transactions_total: float
    nb_acteurs: int
    nb_lots: int


class HomeWidgetsOut(BaseModel):
    gold_price_value: float | None = None
    gold_price_currency: str = "MGA"
    gold_price_unit: str = "g"
    gold_price_source: str | None = None
    gold_price_updated_at: str | None = None
    institutional_message: str | None = None
    institutional_message_version: int | None = None
    institutional_message_updated_at: str | None = None


class InstitutionalMessageIn(BaseModel):
    message: str
