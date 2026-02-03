from pydantic import BaseModel


class PenaltyCreate(BaseModel):
    violation_case_id: int
    penalty_type: str
    amount: float | None = None


class PenaltyOut(BaseModel):
    id: int
    violation_case_id: int
    penalty_type: str
    amount: float | None = None
    status: str
