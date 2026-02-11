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
