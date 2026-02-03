from pydantic import BaseModel


class InspectionCreate(BaseModel):
    inspected_actor_id: int | None = None
    inspected_lot_id: int | None = None
    inspected_invoice_id: int | None = None
    result: str
    reason_code: str | None = None
    notes: str | None = None
    geo_point_id: int | None = None


class InspectionOut(BaseModel):
    id: int
    inspector_actor_id: int
    inspected_actor_id: int | None = None
    inspected_lot_id: int | None = None
    inspected_invoice_id: int | None = None
    result: str
    reason_code: str | None = None
    notes: str | None = None
