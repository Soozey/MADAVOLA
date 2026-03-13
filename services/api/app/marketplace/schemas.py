from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceOfferCreate(BaseModel):
    offer_type: str  # sell|buy
    filiere: str
    lot_id: int | None = None
    product_type: str
    quantity: float = Field(gt=0)
    unit: str
    unit_price: float = Field(gt=0)
    currency: str = "MGA"
    location_commune_id: int | None = None
    expires_at: datetime | None = None
    notes: str | None = None


class MarketplaceOfferOut(BaseModel):
    id: int
    actor_id: int
    actor_name: str | None = None
    offer_type: str
    filiere: str
    lot_id: int | None = None
    product_type: str
    quantity: float
    unit: str
    unit_price: float
    currency: str
    location_commune_id: int | None = None
    status: str
    expires_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
