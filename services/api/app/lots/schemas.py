from datetime import datetime

from pydantic import BaseModel


class LotCreate(BaseModel):
    filiere: str = "OR"
    product_type: str
    unit: str
    quantity: float
    declare_geo_point_id: int
    declared_by_actor_id: int


class LotOut(BaseModel):
    id: int
    filiere: str
    product_type: str
    unit: str
    quantity: float
    declared_at: datetime
    declared_by_actor_id: int
    current_owner_actor_id: int
    status: str
    declare_geo_point_id: int


class LotTransfer(BaseModel):
    new_owner_actor_id: int
    payment_request_id: int


class LotConsolidate(BaseModel):
    lot_ids: list[int]
    product_type: str
    unit: str
    declare_geo_point_id: int


class LotSplit(BaseModel):
    quantities: list[float]
