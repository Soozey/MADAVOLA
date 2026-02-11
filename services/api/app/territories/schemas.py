from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RegionOut(BaseModel):
    id: int | None = None  # présent quand utilisé pour dashboards / sélecteurs
    code: str
    name: str


class DistrictOut(BaseModel):
    code: str
    name: str
    region_code: str


class CommuneOut(BaseModel):
    code: str
    name: str
    district_code: str
    commune_mobile_money_msisdn: Optional[str] = None


class FokontanyOut(BaseModel):
    code: Optional[str] = None
    name: str
    commune_code: str


class TerritoryVersionOut(BaseModel):
    version_tag: str
    source_filename: str
    checksum_sha256: str
    status: str
    imported_at: datetime
    activated_at: Optional[datetime] = None


class TerritoryImportResult(BaseModel):
    version_tag: str
    regions: int
    districts: int
    communes: int
    fokontany: int
