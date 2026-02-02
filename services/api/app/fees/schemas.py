from pydantic import BaseModel


class FeeCreate(BaseModel):
    fee_type: str
    actor_id: int
    commune_id: int
    amount: float
    currency: str = "MGA"


class FeeOut(BaseModel):
    id: int
    fee_type: str
    actor_id: int
    commune_id: int
    amount: float
    currency: str
    status: str
