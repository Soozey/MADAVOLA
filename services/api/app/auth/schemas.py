from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    must_change_password: bool = False


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
    surnom: str | None = None
    telephone: str
    email: str
    status: str
    cin: str | None
    cin_date_delivrance: date | None = None
    date_naissance: date | None = None
    adresse_text: str | None = None
    photo_profile_url: str | None = None
    nif: str | None
    stat: str | None
    rccm: str | None
    region: TerritoryInfo | None
    district: TerritoryInfo | None
    commune: TerritoryInfo | None
    fokontany: TerritoryInfo | None
    roles: list[ActorRoleInfo]
    filieres: list[str]
    primary_role: str | None = None
    must_change_password: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ActorProfilePatch(BaseModel):
    nom: str | None = None
    prenoms: str | None = None
    date_naissance: date | None = None
    adresse_text: str | None = None
    cin: str | None = None
    cin_date_delivrance: date | None = None
    commune_code: str | None = None
    fokontany_code: str | None = None
