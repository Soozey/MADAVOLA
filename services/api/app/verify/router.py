"""
Endpoints publics de vérification (sans auth) pour le scan QR par les contrôleurs.
Le QR sur la carte orpailleur/collecteur pointe vers la page front /verify/actor/:id
qui appelle GET /api/v1/verify/actor/:id pour afficher l'identité.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.invoice import Invoice
from app.models.lot import Lot
from app.models.territory import Commune
from app.verify.schemas import ActorVerifyOut, InvoiceVerifyOut, LotVerifyOut

router = APIRouter(prefix=f"{settings.api_prefix}/verify", tags=["verify"])


@router.get("/actor/{actor_id}", response_model=ActorVerifyOut)
def verify_actor(actor_id: int, db: Session = Depends(get_db)):
    """
    Vérification publique d'un acteur (scan QR par contrôleur).
    Retourne les infos minimales : id, nom, prénoms, statut, commune.
    Pas d'authentification requise pour permettre le scan sur le terrain.
    """
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    commune = db.query(Commune).filter_by(id=actor.commune_id).first() if actor.commune_id else None
    return ActorVerifyOut(
        id=actor.id,
        nom=actor.nom,
        prenoms=actor.prenoms,
        statut=actor.status,
        commune_code=commune.code if commune else "",
        type_personne=actor.type_personne,
    )


@router.get("/lot/{lot_id}", response_model=LotVerifyOut)
def verify_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    return LotVerifyOut(
        id=lot.id,
        status=lot.status,
        current_owner_actor_id=lot.current_owner_actor_id,
        declared_by_actor_id=lot.declared_by_actor_id,
        filiere=lot.filiere,
        product_type=lot.product_type,
        quantity=float(lot.quantity),
        unit=lot.unit,
        declaration_receipt_number=lot.declaration_receipt_number,
        qr_code=lot.qr_code,
    )


@router.get("/invoice/{invoice_ref}", response_model=InvoiceVerifyOut)
def verify_invoice(invoice_ref: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_ref).first()
    if not invoice and invoice_ref.isdigit():
        invoice = db.query(Invoice).filter(Invoice.id == int(invoice_ref)).first()
    if not invoice:
        raise bad_request("facture_introuvable")
    return InvoiceVerifyOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        transaction_id=invoice.transaction_id,
        seller_actor_id=invoice.seller_actor_id,
        buyer_actor_id=invoice.buyer_actor_id,
        total_amount=float(invoice.total_amount),
        status=invoice.status,
        qr_code=invoice.qr_code,
    )
