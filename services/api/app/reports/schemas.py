from datetime import date

from pydantic import BaseModel


class ReportDateRange(BaseModel):
    date_from: date | None = None
    date_to: date | None = None


class CommuneReportOut(BaseModel):
    commune_id: int
    volume_created: float
    transactions_total: float


class ActorReportOut(BaseModel):
    actor_id: int
    volume_created: float
    transactions_total: float


class NationalReportOut(BaseModel):
    volume_created: float
    transactions_total: float
