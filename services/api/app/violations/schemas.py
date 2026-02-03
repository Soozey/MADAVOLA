from pydantic import BaseModel


class ViolationCreate(BaseModel):
    inspection_id: int
    violation_type: str
    legal_basis_ref: str | None = None


class ViolationOut(BaseModel):
    id: int
    inspection_id: int
    violation_type: str
    legal_basis_ref: str | None = None
    status: str
