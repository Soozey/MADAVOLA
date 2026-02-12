from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class TerritoryInfo(BaseModel):
    id: int
    code: str
    name: str


class ActorRoleInfo(BaseModel):
    id: int
    role: str
    status: str
    valid_from: datetime | None
    valid_to: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ActorProfile(BaseModel):
    id: int
    type_personne: str
    nom: str
    prenoms: str | None
    telephone: str
    email: str
    status: str
    cin: str | None
    nif: str | None
    stat: str | None
    rccm: str | None
    region: TerritoryInfo | None
    district: TerritoryInfo | None
    commune: TerritoryInfo | None
    fokontany: TerritoryInfo | None
    roles: list[ActorRoleInfo]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
