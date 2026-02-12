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


class InvoiceVerifyOut(BaseModel):
    id: int
    invoice_number: str
    transaction_id: int
    seller_actor_id: int
    buyer_actor_id: int
    total_amount: float
    status: str
    qr_code: str | None = None
