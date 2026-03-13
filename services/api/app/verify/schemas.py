from pydantic import BaseModel


class ActorVerifyOut(BaseModel):
    """Informations minimales pour vérification par scan QR (carte orpailleur/collecteur)."""
    id: int
    nom: str
    prenoms: str | None
    statut: str
    commune_code: str
    type_personne: str


class LotVerifyOut(BaseModel):
    id: int
    status: str
    current_owner_actor_id: int
    declared_by_actor_id: int
    filiere: str
    product_type: str
    quantity: float
    unit: str
    declaration_receipt_number: str | None = None
    qr_code: str | None = None
    lot_number: str | None = None
    traceability_id: str | None = None
    origin_reference: str | None = None
    previous_block_hash: str | None = None
    current_block_hash: str | None = None
    wood_classification: str | None = None
    cites_laf_status: str | None = None
    cites_ndf_status: str | None = None
    cites_international_status: str | None = None
    destruction_status: str | None = None
    transaction_history: list[str] = []


class InvoiceVerifyOut(BaseModel):
    id: int
    invoice_number: str
    transaction_id: int
    seller_actor_id: int
    buyer_actor_id: int
    filiere: str | None = None
    region_code: str | None = None
    origin_reference: str | None = None
    lot_references: list[str] = []
    subtotal_ht: float | None = None
    taxes_total: float | None = None
    total_ttc: float | None = None
    total_amount: float
    status: str
    qr_code: str | None = None
    invoice_hash: str | None = None
    previous_invoice_hash: str | None = None
    internal_signature: str | None = None
    receipt_number: str | None = None
