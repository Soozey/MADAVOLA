from datetime import date

from pydantic import BaseModel, Field


class ActorCreate(BaseModel):
    type_personne: str
    nom: str
    prenoms: str | None = None
    cin: str | None = None
    cin_date_delivrance: date | None = None
    date_naissance: date | None = None
    surnom: str | None = None
    adresse_text: str | None = None
    nif: str | None = None
    stat: str | None = None
    rccm: str | None = None
    telephone: str
    email: str | None = None
    password: str
    region_code: str
    district_code: str
    commune_code: str
    fokontany_code: str | None = None
    geo_point_id: int
    roles: list[str]
    filieres: list[str] | None = None


class ActorStatusUpdate(BaseModel):
    status: str  # "active" | "rejected"


class ActorOut(BaseModel):
    id: int
    type_personne: str
    nom: str
    prenoms: str | None = None
    surnom: str | None = None
    telephone: str
    email: str | None = None
    status: str
    cin: str | None = None
    cin_date_delivrance: date | None = None
    date_naissance: date | None = None
    adresse_text: str | None = None
    photo_profile_url: str | None = None
    region_code: str
    district_code: str
    commune_code: str
    fokontany_code: str | None = None
    opening_fee_id: int | None = None
    opening_fee_status: str | None = None
    filieres: list[str] = Field(default_factory=list)
    laissez_passer_access_status: str
    agrement_status: str
    sig_oc_access_status: str


class ActorKYCCreate(BaseModel):
    pieces: list[str] = Field(default_factory=list)
    note: str | None = None


class ActorKYCOut(BaseModel):
    id: int
    actor_id: int
    pieces: list[str] = Field(default_factory=list)
    verified_by: int | None = None
    verified_at: str | None = None
    note: str | None = None


class ActorWalletCreate(BaseModel):
    provider: str
    operator_name: str | None = None
    account_ref: str
    is_primary: bool = False


class ActorWalletOut(BaseModel):
    id: int
    actor_id: int
    provider: str
    operator_name: str | None = None
    account_ref: str
    is_primary: bool
    status: str


class CommuneProfilePatch(BaseModel):
    mobile_money_account_ref: str | None = None
    receiver_name: str | None = None
    receiver_phone: str | None = None
    active: bool | None = None


class CommuneProfileOut(BaseModel):
    commune_id: int
    mobile_money_account_ref: str | None = None
    receiver_name: str | None = None
    receiver_phone: str | None = None
    active: bool
