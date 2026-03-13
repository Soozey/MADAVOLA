from datetime import datetime

from pydantic import BaseModel


class AuthorizationCreate(BaseModel):
    filiere: str = "PIERRE"
    authorization_type: str
    numero: str
    valid_from: datetime
    valid_to: datetime
    status: str = "active"
    notes: str | None = None


class AuthorizationOut(BaseModel):
    id: int
    actor_id: int
    filiere: str
    authorization_type: str
    numero: str
    valid_from: datetime
    valid_to: datetime
    status: str
    notes: str | None = None
