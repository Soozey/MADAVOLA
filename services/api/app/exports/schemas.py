from pydantic import BaseModel


class ExportCreate(BaseModel):
    destination: str | None = None
    total_weight: float | None = None


class ExportOut(BaseModel):
    id: int
    status: str
    destination: str | None = None
    total_weight: float | None = None
    created_by_actor_id: int
