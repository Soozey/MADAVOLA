from pydantic import BaseModel


class ActorCreate(BaseModel):
    type_personne: str
    nom: str
    prenoms: str | None = None
    cin: str | None = None
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


class ActorStatusUpdate(BaseModel):
    status: str  # "active" | "rejected"


class ActorOut(BaseModel):
    id: int
    type_personne: str
    nom: str
    prenoms: str | None = None
    telephone: str
    email: str | None = None
    status: str
    region_code: str
    district_code: str
    commune_code: str
    fokontany_code: str | None = None