from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemConfigCreate(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None


class SystemConfigUpdate(BaseModel):
    value: str | None = None
    description: str | None = None


class SystemConfigOut(BaseModel):
    id: int
    key: str
    value: str | None
    description: str | None
    updated_by_actor_id: int
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActorRoleAssign(BaseModel):
    role: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class ActorRoleUpdate(BaseModel):
    status: str | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class ActorRoleOut(BaseModel):
    id: int
    actor_id: int
    role: str
    status: str
    valid_from: datetime | None
    valid_to: datetime | None

    model_config = ConfigDict(from_attributes=True)
