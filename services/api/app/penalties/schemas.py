from pydantic import BaseModel


class PenaltyCreate(BaseModel):
    violation_case_id: int
    penalty_type: str
    amount: float | None = None
    action_on_lot: str | None = None  # none | block | seize
    seized_to_actor_id: int | None = None


class PenaltyOut(BaseModel):
    id: int
    violation_case_id: int
    penalty_type: str
    amount: float | None = None
    status: str
    action_on_lot: str | None = None
