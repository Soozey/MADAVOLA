from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.logger import write_audit
from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.common.receipts import build_simple_pdf
from app.common.card_identity import (
    build_card_number,
    build_prefixed_uid,
    canonical_json,
    sha256_hex,
    sign_hmac_sha256,
)
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.document import Document
from app.models.fee import Fee
from app.models.or_compliance import (
    CollectorAffiliationAgreement,
    CollectorCard,
    CollectorCardDocument,
    CollectorSemiAnnualReport,
    ComptoirLicense,
    ComplianceNotification,
    KaraBolamenaCard,
    KaraProductionLog,
    OrTariffConfig,
)
from app.models.territory import Commune, TerritoryVersion
from app.or_compliance.reminders import run_expiry_reminders
from app.or_compliance.schemas import (
    CardQueueItemOut,
    CardRequestIn,
    CardDecisionIn,
    CardRenderOut,
    CollectorAffiliationCreate,
    CollectorCardCreate,
    CollectorCardDecision,
    CollectorCardOut,
    CollectorDocumentAttach,
    ComptoirLicenseCreate,
    ComptoirLicenseOut,
    ComptoirLicenseStatusPatch,
    KaraCardCreate,
    KaraCardDecision,
    KaraCardOut,
    ProductionLogCreate,
    ProductionLogOut,
    ReminderRunOut,
    TariffCreate,
    TariffOut,
    MyCardsOut,
)

router = APIRouter(prefix=f"{settings.api_prefix}/or-compliance", tags=["or_compliance"])

COLLECTOR_REQUIRED_DOCS = [
    "formulaire_signe",
    "justificatif_residence_moins_3_mois",
    "casier_judiciaire_b3",
    "cin_certifiee",
    "carte_fiscale",
    "carte_identification_etablissement",
    "photo_4x4_1",
    "photo_4x4_2",
]

STATUS_PENDING_PAYMENT = "pending_payment"
STATUS_PENDING_VALIDATION = "pending_validation"
STATUS_VALIDATED = "validated"
STATUS_REJECTED = "rejected"
STATUS_EXPIRED = "expired"
STATUS_SUSPENDED = "suspended"
STATUS_REVOKED = "revoked"


def _display_status(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in {"active", STATUS_VALIDATED}:
        return STATUS_VALIDATED
    if raw in {"pending", STATUS_PENDING_PAYMENT}:
        return STATUS_PENDING_PAYMENT
    if raw in {STATUS_PENDING_VALIDATION}:
        return STATUS_PENDING_VALIDATION
    if raw in {"withdrawn", STATUS_REVOKED}:
        return STATUS_REVOKED
    if raw in {STATUS_REJECTED, STATUS_EXPIRED, STATUS_SUSPENDED}:
        return raw
    return STATUS_PENDING_PAYMENT


def _storage_status(value: str) -> str:
    display = _display_status(value)
    if display == STATUS_VALIDATED:
        return "active"
    if display == STATUS_REVOKED:
        return "withdrawn"
    if display == STATUS_PENDING_PAYMENT:
        return "pending"
    return display


def _tariff_amount(db: Session, card_type: str, commune_id: int | None, now: datetime) -> Decimal:
    rows = (
        db.query(OrTariffConfig)
        .filter(
            OrTariffConfig.card_type == card_type,
            OrTariffConfig.status == "active",
            OrTariffConfig.effective_from <= now,
        )
        .order_by(OrTariffConfig.commune_id.desc(), OrTariffConfig.effective_from.desc())
        .all()
    )
    for row in rows:
        if row.effective_to and row.effective_to < now:
            continue
        if row.commune_id is None or row.commune_id == commune_id:
            return Decimal(str(row.amount))
    if card_type == "collector_card":
        return Decimal("10000")
    if card_type == "kara_bolamena":
        return Decimal("4000")
    return Decimal("10000")


def _to_kara_out(card: KaraBolamenaCard) -> KaraCardOut:
    return KaraCardOut(
        id=card.id,
        actor_id=card.actor_id,
        commune_id=card.commune_id,
        card_uid=card.card_uid,
        card_number=card.card_number,
        unique_identifier=card.unique_identifier,
        status=_display_status(card.status),
        cin=card.cin,
        nationality=card.nationality,
        residence_verified=card.residence_verified,
        tax_compliant=card.tax_compliant,
        zone_allowed=card.zone_allowed,
        public_order_clear=card.public_order_clear,
        fee_id=card.fee_id,
        issued_at=card.issued_at,
        validated_at=card.validated_at,
        expires_at=card.expires_at,
        revoked_at=card.revoked_at,
        qr_value=card.qr_value,
        qr_payload_hash=card.qr_payload_hash,
        qr_signature=card.qr_signature,
        front_document_id=card.front_document_id,
        back_document_id=card.back_document_id,
    )


def _to_collector_out(card: CollectorCard) -> CollectorCardOut:
    return CollectorCardOut(
        id=card.id,
        actor_id=card.actor_id,
        issuing_commune_id=card.issuing_commune_id,
        card_uid=card.card_uid,
        card_number=card.card_number,
        role="bijoutier" if _is_bijoutier_card(card) else "collecteur",
        status=_display_status(card.status),
        fee_id=card.fee_id,
        issued_at=card.issued_at,
        validated_at=card.validated_at,
        expires_at=card.expires_at,
        revoked_at=card.revoked_at,
        affiliation_deadline_at=card.affiliation_deadline_at,
        affiliation_submitted_at=card.affiliation_submitted_at,
        laissez_passer_blocked_reason=card.laissez_passer_blocked_reason,
        qr_value=card.qr_value,
        qr_payload_hash=card.qr_payload_hash,
        qr_signature=card.qr_signature,
        front_document_id=card.front_document_id,
        back_document_id=card.back_document_id,
    )


@router.post("/tariffs", response_model=TariffOut, status_code=201)
def create_tariff(
    payload: TariffCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin", "commune_agent"})),
):
    row = OrTariffConfig(
        card_type=payload.card_type,
        commune_id=payload.commune_id,
        amount=payload.amount,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="active",
        configured_by_actor_id=current_actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TariffOut(
        id=row.id,
        card_type=row.card_type,
        commune_id=row.commune_id,
        amount=float(row.amount),
        min_amount=float(row.min_amount) if row.min_amount is not None else None,
        max_amount=float(row.max_amount) if row.max_amount is not None else None,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        status=row.status,
    )


@router.get("/tariffs", response_model=list[TariffOut])
def list_tariffs(db: Session = Depends(get_db), _actor=Depends(get_current_actor)):
    rows = db.query(OrTariffConfig).order_by(OrTariffConfig.effective_from.desc()).all()
    return [
        TariffOut(
            id=row.id,
            card_type=row.card_type,
            commune_id=row.commune_id,
            amount=float(row.amount),
            min_amount=float(row.min_amount) if row.min_amount is not None else None,
            max_amount=float(row.max_amount) if row.max_amount is not None else None,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/cards/request", status_code=201)
def request_card(
    payload: CardRequestIn,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    card_type = (payload.card_type or "").strip().lower()
    if card_type == "kara_bolamena":
        if not payload.cin:
            raise bad_request("cin_obligatoire")
        return request_kara_card(
            KaraCardCreate(
                actor_id=payload.actor_id,
                commune_id=payload.commune_id,
                cin=payload.cin,
                notes=payload.notes,
            ),
            db,
            current_actor,
        )
    if card_type in {"collector_card", "bijoutier_card"}:
        notes = payload.notes
        if card_type == "bijoutier_card":
            notes = ((notes or "") + " [role=bijoutier]").strip()
        return request_collector_card(
            CollectorCardCreate(
                actor_id=payload.actor_id,
                issuing_commune_id=payload.commune_id,
                notes=notes,
            ),
            db,
            current_actor,
        )
    raise bad_request("type_carte_invalide")


@router.post("/cards/{card_id}/validate")
def validate_card(
    card_id: int,
    payload: CardDecisionIn,
    card_type: str = "kara_bolamena",
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune", "commune_agent", "com_admin", "com_agent", "com"})),
):
    normalized = (card_type or "").strip().lower()
    if normalized == "kara_bolamena":
        return decide_kara_card(
            card_id=card_id,
            payload=KaraCardDecision(decision=payload.decision, notes=payload.notes),
            db=db,
            current_actor=current_actor,
        )
    if normalized in {"collector_card", "bijoutier_card"}:
        return decide_collector_card(
            card_id=card_id,
            payload=CollectorCardDecision(decision=payload.decision, notes=payload.notes),
            db=db,
            current_actor=current_actor,
        )
    raise bad_request("type_carte_invalide")


@router.get("/cards/{card_id}/render", response_model=CardRenderOut)
def render_card_side(
    card_id: int,
    side: str = "front",
    card_type: str = "kara_bolamena",
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    resolved = _load_card_by_type(db, card_type, card_id)
    if not resolved:
        raise bad_request("carte_introuvable")
    kind, card = resolved
    actor_id = card.actor_id
    if not _is_actor_allowed_for_card(db, current_actor.id, actor_id):
        raise bad_request("acces_refuse")
    _ensure_card_documents(db, card, kind)
    db.commit()
    if side not in {"front", "back"}:
        raise bad_request("side_invalide")
    document_id = card.front_document_id if side == "front" else card.back_document_id
    return CardRenderOut(
        card_id=card.id,
        card_type=kind,
        side=side,
        status=_display_status(card.status),
        card_number=card.card_number,
        document_id=document_id,
        download_url=f"{settings.api_prefix}/documents/{document_id}/download" if document_id else None,
        qr_value=card.qr_value,
        qr_payload_hash=card.qr_payload_hash,
        qr_signature=card.qr_signature,
    )


@router.post("/kara-cards", response_model=KaraCardOut, status_code=201)
def request_kara_card(
    payload: KaraCardCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_active_commune(db, payload.commune_id):
        raise bad_request("commune_invalide")
    if current_actor.id != payload.actor_id and current_actor.commune_id != payload.commune_id:
        raise bad_request("acces_refuse")
    actor = db.query(Actor).filter_by(id=payload.actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")

    now = datetime.now(timezone.utc)
    fee = Fee(
        fee_type="kara_bolamena_right",
        actor_id=payload.actor_id,
        commune_id=payload.commune_id,
        amount=_tariff_amount(db, "kara_bolamena", payload.commune_id, now),
        currency="MGA",
        status="pending",
    )
    db.add(fee)
    db.flush()

    commune = db.query(Commune).filter_by(id=payload.commune_id).first()
    commune_code = commune.code if commune else "COMM"
    card_uid = build_prefixed_uid("MDV-CARD")
    card_number = build_card_number(
        filiere="OR",
        commune_code=commune_code,
        seq=_next_card_sequence(db, payload.commune_id, now),
        now=now,
    )

    card = KaraBolamenaCard(
        actor_id=payload.actor_id,
        commune_id=payload.commune_id,
        card_uid=card_uid,
        card_number=card_number,
        unique_identifier=f"KARA-{now.strftime('%Y%m%d')}-{payload.actor_id}-{fee.id}",
        status=_storage_status(STATUS_PENDING_PAYMENT),
        nationality=(payload.nationality or "mg").lower(),
        cin=payload.cin,
        residence_verified=payload.residence_verified,
        tax_compliant=payload.tax_compliant,
        zone_allowed=payload.zone_allowed,
        public_order_clear=payload.public_order_clear,
        fee_id=fee.id,
        notes=payload.notes,
    )
    db.add(card)
    write_audit(
        db,
        actor_id=current_actor.id,
        action="kara_card_requested",
        entity_type="kara_card",
        entity_id="pending",
        meta={"target_actor_id": payload.actor_id, "commune_id": payload.commune_id},
    )
    db.commit()
    db.refresh(card)
    return _to_kara_out(card)


@router.get("/kara-cards", response_model=list[KaraCardOut])
def list_kara_cards(
    actor_id: int | None = None,
    status: str | None = None,
    commune_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(KaraBolamenaCard)
    if actor_id:
        if actor_id != current_actor.id:
            require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin"})(current_actor, db)
        query = query.filter(KaraBolamenaCard.actor_id == actor_id)
    elif commune_id is not None:
        require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin"})(current_actor, db)
        query = query.filter(KaraBolamenaCard.commune_id == commune_id)
    else:
        query = query.filter(KaraBolamenaCard.actor_id == current_actor.id)
    if status:
        mapped = _storage_status(status)
        query = query.filter(KaraBolamenaCard.status == mapped)
    rows = query.order_by(KaraBolamenaCard.created_at.desc()).all()
    return [_to_kara_out(row) for row in rows]


@router.patch("/kara-cards/{card_id}/decision", response_model=KaraCardOut)
def decide_kara_card(
    card_id: int,
    payload: KaraCardDecision,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune", "commune_agent", "com_admin"})),
):
    card = db.query(KaraBolamenaCard).filter_by(id=card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    decision = (payload.decision or "").strip().lower()
    if decision not in {"approved", "rejected", "suspended", "withdrawn", "revoked"}:
        raise bad_request("decision_invalide")

    if decision == "approved":
        if card.nationality != "mg" or not card.residence_verified or not card.tax_compliant:
            raise bad_request("eligibilite_kara_non_validee")
        if not card.zone_allowed or not card.public_order_clear:
            raise bad_request("eligibilite_kara_non_validee")
        fee = db.query(Fee).filter_by(id=card.fee_id).first() if card.fee_id else None
        if not fee or fee.status != "paid":
            raise bad_request("frais_ouverture_non_payes")
        now = datetime.now(timezone.utc)
        card.status = _storage_status(STATUS_VALIDATED)
        card.issued_by_actor_id = current_actor.id
        card.validated_by_actor_id = current_actor.id
        card.issued_at = now
        card.validated_at = now
        card.expires_at = now + timedelta(days=365)
        card.revoked_at = None
        _refresh_kara_qr(card, db)
        _ensure_card_documents(db, card, card_type="kara_bolamena")
    else:
        if decision in {"withdrawn", "revoked"}:
            card.status = _storage_status(STATUS_REVOKED)
            card.revoked_at = datetime.now(timezone.utc)
        elif decision == "rejected":
            card.status = _storage_status(STATUS_REJECTED)
        else:
            card.status = _storage_status(decision)
    if payload.notes:
        card.notes = payload.notes
    write_audit(
        db,
        actor_id=current_actor.id,
        action="kara_card_decision",
        entity_type="kara_card",
        entity_id=str(card.id),
        meta={"decision": decision},
    )
    db.commit()
    db.refresh(card)
    return _to_kara_out(card)


@router.post("/kara-production-logs", response_model=ProductionLogOut, status_code=201)
def create_production_log(
    payload: ProductionLogCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    card = db.query(KaraBolamenaCard).filter_by(id=payload.card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    if _display_status(card.status) != STATUS_VALIDATED:
        raise bad_request("carte_invalide")
    if current_actor.id != card.actor_id:
        raise bad_request("acces_refuse")
    row = KaraProductionLog(
        card_id=payload.card_id,
        log_date=payload.log_date,
        zone_name=payload.zone_name,
        quantity_gram=payload.quantity_gram,
        notes=payload.notes,
        submitted_by_actor_id=current_actor.id,
    )
    db.add(row)
    write_audit(
        db,
        actor_id=current_actor.id,
        action="kara_production_logged",
        entity_type="kara_card",
        entity_id=str(card.id),
        meta={"quantity_gram": payload.quantity_gram, "date": payload.log_date.isoformat()},
    )
    db.commit()
    db.refresh(row)
    return ProductionLogOut(
        id=row.id,
        card_id=row.card_id,
        log_date=row.log_date,
        zone_name=row.zone_name,
        quantity_gram=float(row.quantity_gram),
        notes=row.notes,
    )


@router.post("/collector-cards", response_model=CollectorCardOut, status_code=201)
def request_collector_card(
    payload: CollectorCardCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_active_commune(db, payload.issuing_commune_id):
        raise bad_request("commune_invalide")
    if current_actor.id != payload.actor_id and current_actor.commune_id != payload.issuing_commune_id:
        raise bad_request("acces_refuse")
    active_or_pending = (
        db.query(CollectorCard)
        .filter(
            CollectorCard.actor_id == payload.actor_id,
            CollectorCard.status.in_(["pending", "active"]),
        )
        .all()
    )
    if len(active_or_pending) >= 5:
        raise bad_request("limite_cartes_collecteur_atteinte")
    if any(c.issuing_commune_id == payload.issuing_commune_id for c in active_or_pending):
        raise bad_request("commune_deja_couverte")

    now = datetime.now(timezone.utc)
    fee = Fee(
        fee_type="collector_card_right",
        actor_id=payload.actor_id,
        commune_id=payload.issuing_commune_id,
        amount=_tariff_amount(db, "collector_card", payload.issuing_commune_id, now),
        currency="MGA",
        status="pending",
    )
    db.add(fee)
    db.flush()
    commune = db.query(Commune).filter_by(id=payload.issuing_commune_id).first()
    commune_code = commune.code if commune else "COMM"
    card_uid = build_prefixed_uid("MDV-CARD")
    actor_roles = _active_roles(db, payload.actor_id)
    role_hint = "bijoutier" if ("bijoutier" in actor_roles or "bijoutier" in (payload.notes or "").lower()) else "collecteur"
    card_number = build_card_number(
        filiere="OR",
        commune_code=commune_code,
        seq=_next_card_sequence(db, payload.issuing_commune_id, now),
        now=now,
    )
    card = CollectorCard(
        actor_id=payload.actor_id,
        issuing_commune_id=payload.issuing_commune_id,
        card_uid=card_uid,
        card_number=card_number,
        status=_storage_status(STATUS_PENDING_PAYMENT),
        fee_id=fee.id,
        laissez_passer_blocked_reason="affiliation_non_communiquee",
        qr_value=f"role={role_hint}",
    )
    db.add(card)
    db.flush()
    for doc_type in COLLECTOR_REQUIRED_DOCS:
        db.add(
            CollectorCardDocument(
                collector_card_id=card.id,
                doc_type=doc_type,
                required=True,
                status="missing",
                notes="piece_a_fournir",
            )
        )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="collector_card_requested",
        entity_type="collector_card",
        entity_id=str(card.id),
        meta={"actor_id": payload.actor_id, "commune_id": payload.issuing_commune_id},
    )
    db.commit()
    db.refresh(card)
    return _to_collector_out(card)


@router.get("/collector-cards", response_model=list[CollectorCardOut])
def list_collector_cards(
    actor_id: int | None = None,
    status: str | None = None,
    commune_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(CollectorCard)
    if actor_id:
        if actor_id != current_actor.id:
            require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin", "com_agent"})(current_actor, db)
        query = query.filter(CollectorCard.actor_id == actor_id)
    elif commune_id is not None:
        require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin", "com_agent"})(current_actor, db)
        query = query.filter(CollectorCard.issuing_commune_id == commune_id)
    else:
        query = query.filter(CollectorCard.actor_id == current_actor.id)
    if status:
        mapped = _storage_status(status)
        query = query.filter(CollectorCard.status == mapped)
    rows = query.order_by(CollectorCard.created_at.desc()).all()
    return [_to_collector_out(row) for row in rows]


@router.post("/collector-cards/{card_id}/documents", response_model=CollectorCardOut)
def attach_collector_document(
    card_id: int,
    payload: CollectorDocumentAttach,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    card = db.query(CollectorCard).filter_by(id=card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    if current_actor.id != card.actor_id:
        raise bad_request("acces_refuse")
    row = (
        db.query(CollectorCardDocument)
        .filter(CollectorCardDocument.collector_card_id == card.id, CollectorCardDocument.doc_type == payload.doc_type)
        .first()
    )
    if not row:
        raise bad_request("piece_inconnue")
    row.document_id = payload.document_id
    row.status = "uploaded"
    db.commit()
    db.refresh(card)
    return _to_collector_out(card)


@router.patch("/collector-cards/{card_id}/decision", response_model=CollectorCardOut)
def decide_collector_card(
    card_id: int,
    payload: CollectorCardDecision,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin", "com_agent", "commune", "commune_agent"})),
):
    card = db.query(CollectorCard).filter_by(id=card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    decision = (payload.decision or "").strip().lower()
    if decision not in {"approved", "rejected", "suspended", "withdrawn", "revoked"}:
        raise bad_request("decision_invalide")
    if decision == "approved":
        missing_required = (
            db.query(CollectorCardDocument.id)
            .filter(
                CollectorCardDocument.collector_card_id == card.id,
                CollectorCardDocument.required == True,  # noqa: E712
                CollectorCardDocument.status == "missing",
            )
            .first()
        )
        if missing_required:
            raise bad_request("pieces_obligatoires_manquantes")
        fee = db.query(Fee).filter_by(id=card.fee_id).first() if card.fee_id else None
        if not fee or fee.status != "paid":
            raise bad_request("frais_ouverture_non_payes")
        now = datetime.now(timezone.utc)
        card.status = _storage_status(STATUS_VALIDATED)
        card.issued_by_actor_id = current_actor.id
        card.validated_by_actor_id = current_actor.id
        card.issued_at = now
        card.validated_at = now
        card.expires_at = now + timedelta(days=365)
        card.affiliation_deadline_at = now + timedelta(days=90)
        card.revoked_at = None
        _refresh_collector_qr(card, db)
        _ensure_card_documents(db, card, card_type="collector_card")
    else:
        if decision in {"withdrawn", "revoked"}:
            card.status = _storage_status(STATUS_REVOKED)
            card.revoked_at = datetime.now(timezone.utc)
        elif decision == "rejected":
            card.status = _storage_status(STATUS_REJECTED)
        else:
            card.status = _storage_status(decision)
    if payload.notes:
        card.laissez_passer_blocked_reason = payload.notes
    db.commit()
    db.refresh(card)
    return _to_collector_out(card)


@router.get("/cards/my", response_model=MyCardsOut)
def get_my_cards(
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    kara = (
        db.query(KaraBolamenaCard)
        .filter(KaraBolamenaCard.actor_id == current_actor.id)
        .order_by(KaraBolamenaCard.created_at.desc())
        .all()
    )
    collector = (
        db.query(CollectorCard)
        .filter(CollectorCard.actor_id == current_actor.id)
        .order_by(CollectorCard.created_at.desc())
        .all()
    )
    return MyCardsOut(
        kara_cards=[_to_kara_out(x) for x in kara],
        collector_cards=[_to_collector_out(x) for x in collector],
    )


@router.get("/cards/commune-queue", response_model=list[CardQueueItemOut])
def get_commune_queue(
    status: str = STATUS_PENDING_VALIDATION,
    commune_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin", "com_agent"})),
):
    target_commune = commune_id or current_actor.commune_id
    if not target_commune and current_actor.id:
        raise bad_request("commune_invalide")
    if target_commune and not _is_active_commune(db, target_commune):
        raise bad_request("commune_invalide")

    normalized_status = (status or "").strip().lower()
    include_pending_both = normalized_status == "pending"
    filter_status = _storage_status(status)
    kara_rows = (
        db.query(KaraBolamenaCard, Fee, Actor)
        .join(Fee, Fee.id == KaraBolamenaCard.fee_id, isouter=True)
        .join(Actor, Actor.id == KaraBolamenaCard.actor_id)
        .filter(
            KaraBolamenaCard.commune_id == target_commune,
            KaraBolamenaCard.status.in_(["pending", "pending_validation"]) if include_pending_both else KaraBolamenaCard.status == filter_status,
        )
        .all()
    )
    collector_rows = (
        db.query(CollectorCard, Fee, Actor)
        .join(Fee, Fee.id == CollectorCard.fee_id, isouter=True)
        .join(Actor, Actor.id == CollectorCard.actor_id)
        .filter(
            CollectorCard.issuing_commune_id == target_commune,
            CollectorCard.status.in_(["pending", "pending_validation"]) if include_pending_both else CollectorCard.status == filter_status,
        )
        .all()
    )
    out: list[CardQueueItemOut] = []
    for card, fee, actor in kara_rows:
        out.append(
            CardQueueItemOut(
                card_id=card.id,
                card_type="kara_bolamena",
                actor_id=card.actor_id,
                commune_id=card.commune_id,
                status=_display_status(card.status),
                fee_id=card.fee_id,
                fee_status=fee.status if fee else None,
                created_at=card.created_at,
                actor_name=f"{actor.nom} {actor.prenoms or ''}".strip(),
            )
        )
    for card, fee, actor in collector_rows:
        out.append(
            CardQueueItemOut(
                card_id=card.id,
                card_type="collector_card",
                actor_id=card.actor_id,
                commune_id=card.issuing_commune_id,
                status=_display_status(card.status),
                fee_id=card.fee_id,
                fee_status=fee.status if fee else None,
                created_at=card.created_at,
                actor_name=f"{actor.nom} {actor.prenoms or ''}".strip(),
            )
        )
    out.sort(key=lambda x: x.created_at, reverse=True)
    return out


@router.post("/collector-cards/{card_id}/verify-document", response_model=CollectorCardOut)
def verify_collector_document(
    card_id: int,
    payload: CollectorDocumentAttach,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin", "com_agent"})),
):
    card = db.query(CollectorCard).filter_by(id=card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    row = (
        db.query(CollectorCardDocument)
        .filter(CollectorCardDocument.collector_card_id == card.id, CollectorCardDocument.doc_type == payload.doc_type)
        .first()
    )
    if not row:
        raise bad_request("piece_inconnue")
    row.document_id = payload.document_id
    row.status = "verified"
    row.verified_by_actor_id = current_actor.id
    row.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(card)
    return _to_collector_out(card)


@router.post("/collector-affiliations", response_model=CollectorCardOut, status_code=201)
def submit_collector_affiliation(
    payload: CollectorAffiliationCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    card = db.query(CollectorCard).filter_by(id=payload.collector_card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    if current_actor.id != card.actor_id and current_actor.id != payload.affiliate_actor_id:
        raise bad_request("acces_refuse")
    if payload.affiliate_type not in {"comptoir", "bijouterie"}:
        raise bad_request("affiliation_invalide")
    affiliate = db.query(Actor).filter_by(id=payload.affiliate_actor_id).first()
    if not affiliate:
        raise bad_request("acteur_invalide")

    row = CollectorAffiliationAgreement(
        collector_card_id=card.id,
        affiliate_actor_id=payload.affiliate_actor_id,
        affiliate_type=payload.affiliate_type,
        agreement_ref=payload.agreement_ref,
        signed_at=payload.signed_at,
        communicated_to_com_at=datetime.now(timezone.utc),
        status="submitted",
    )
    db.add(row)
    card.affiliation_submitted_at = datetime.now(timezone.utc)
    card.laissez_passer_blocked_reason = None
    actor = db.query(Actor).filter_by(id=card.actor_id).first()
    if actor:
        actor.laissez_passer_access_status = "active"
    db.commit()
    db.refresh(card)
    return _to_collector_out(card)


@router.post("/collector-cards/{card_id}/semiannual-reports", status_code=201)
def submit_collector_report(
    card_id: int,
    period_label: str,
    report_payload_json: str,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    card = db.query(CollectorCard).filter_by(id=card_id).first()
    if not card:
        raise bad_request("carte_introuvable")
    if current_actor.id != card.actor_id:
        raise bad_request("acces_refuse")
    db.add(
        CollectorSemiAnnualReport(
            collector_card_id=card.id,
            period_label=period_label,
            report_payload_json=report_payload_json,
            status="submitted",
        )
    )
    db.commit()
    return {"status": "ok"}


@router.post("/comptoir-licenses", response_model=ComptoirLicenseOut, status_code=201)
def create_comptoir_license(
    payload: ComptoirLicenseCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin", "com_agent"})),
):
    now = datetime.now(timezone.utc)
    row = ComptoirLicense(
        actor_id=payload.actor_id,
        status="active",
        issued_at=now,
        expires_at=now + timedelta(days=365),
        dtspm_status="ok",
        fx_repatriation_status="ok",
        access_sig_oc_suspended=False,
        cahier_des_charges_ref=payload.cahier_des_charges_ref,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_comptoir_out(row)


def _to_comptoir_out(row: ComptoirLicense) -> ComptoirLicenseOut:
    return ComptoirLicenseOut(
        id=row.id,
        actor_id=row.actor_id,
        status=row.status,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        dtspm_status=row.dtspm_status,
        fx_repatriation_status=row.fx_repatriation_status,
        access_sig_oc_suspended=row.access_sig_oc_suspended,
        cahier_des_charges_ref=row.cahier_des_charges_ref,
        notes=row.notes,
    )


@router.patch("/comptoir-licenses/{license_id}", response_model=ComptoirLicenseOut)
def patch_comptoir_license(
    license_id: int,
    payload: ComptoirLicenseStatusPatch,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin"})),
):
    row = db.query(ComptoirLicense).filter_by(id=license_id).first()
    if not row:
        raise bad_request("licence_introuvable")
    if payload.status:
        row.status = payload.status
    if payload.dtspm_status:
        row.dtspm_status = payload.dtspm_status
        if payload.dtspm_status in {"late", "suspended"}:
            row.status = "suspended"
        if payload.dtspm_status == "cancelled":
            row.status = "cancelled"
    if payload.fx_repatriation_status:
        row.fx_repatriation_status = payload.fx_repatriation_status
        row.access_sig_oc_suspended = payload.fx_repatriation_status in {"late", "suspended"}
    if payload.notes:
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return _to_comptoir_out(row)


@router.post("/reminders/run", response_model=ReminderRunOut)
def run_reminders(
    thresholds: str = "30,7,1",
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "com_admin"})),
):
    parsed = []
    for token in thresholds.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            raise bad_request("seuil_rappel_invalide")
        parsed.append(int(token))
    created = run_expiry_reminders(db, parsed or [30, 7, 1], current_actor.id)
    return ReminderRunOut(created_notifications=created)


@router.get("/notifications")
def list_notifications(
    actor_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(ComplianceNotification)
    if actor_id:
        query = query.filter(ComplianceNotification.actor_id == actor_id)
    else:
        query = query.filter(ComplianceNotification.actor_id == current_actor.id)
    rows = query.order_by(ComplianceNotification.sent_at.desc()).all()
    return [
        {
            "id": row.id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "actor_id": row.actor_id,
            "days_before": row.days_before,
            "message": row.message,
            "status": row.status,
            "sent_at": row.sent_at,
        }
        for row in rows
    ]


def mark_cards_pending_validation_for_fee(db: Session, fee_id: int) -> None:
    if not fee_id:
        return
    kara = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.fee_id == fee_id).all()
    for card in kara:
        if _display_status(card.status) == STATUS_PENDING_PAYMENT:
            card.status = _storage_status(STATUS_PENDING_VALIDATION)
    collector = db.query(CollectorCard).filter(CollectorCard.fee_id == fee_id).all()
    for card in collector:
        if _display_status(card.status) == STATUS_PENDING_PAYMENT:
            card.status = _storage_status(STATUS_PENDING_VALIDATION)


def _load_card_by_type(db: Session, card_type: str, card_id: int):
    normalized = (card_type or "").strip().lower()
    if normalized in {"kara_bolamena", "kara"}:
        card = db.query(KaraBolamenaCard).filter_by(id=card_id).first()
        return ("kara_bolamena", card) if card else None
    if normalized in {"collector_card", "bijoutier_card", "collector"}:
        card = db.query(CollectorCard).filter_by(id=card_id).first()
        return ("collector_card", card) if card else None
    return None


def _is_actor_allowed_for_card(db: Session, requester_actor_id: int, owner_actor_id: int) -> bool:
    if requester_actor_id == owner_actor_id:
        return True
    if (
        db.query(ActorRole.id)
        .filter(ActorRole.actor_id == requester_actor_id, ActorRole.role.in_(["admin", "dirigeant", "com", "com_admin", "com_agent"]))
        .first()
        is not None
    ):
        return True
    requester = db.query(Actor).filter_by(id=requester_actor_id).first()
    owner = db.query(Actor).filter_by(id=owner_actor_id).first()
    if not requester or not owner:
        return False
    return (
        requester.commune_id == owner.commune_id
        and db.query(ActorRole.id).filter(ActorRole.actor_id == requester_actor_id, ActorRole.role == "commune_agent").first() is not None
    )


def _active_roles(db: Session, actor_id: int) -> set[str]:
    rows = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    return {row[0] for row in rows}


def _is_bijoutier_card(card: CollectorCard) -> bool:
    qr_value = card.qr_value or ""
    notes = card.laissez_passer_blocked_reason or ""
    payload = card.qr_payload_json or ""
    return (
        "role=bijoutier" in qr_value
        or '"role":"bijoutier"' in qr_value
        or "bijoutier" in notes.lower()
        or '"role":"bijoutier"' in payload
    )


def _next_card_sequence(db: Session, commune_id: int, now: datetime) -> int:
    kara_count = db.query(KaraBolamenaCard.id).filter(KaraBolamenaCard.commune_id == commune_id).count()
    collector_count = db.query(CollectorCard.id).filter(CollectorCard.issuing_commune_id == commune_id).count()
    # Reserve monotonic sequence per commune/year without destructive renumbering.
    return max(1, kara_count + collector_count + 1)


def _card_payload(db: Session, *, card_type: str, card, actor_id: int, commune_id: int, role: str, filiere: str = "OR") -> dict:
    actor = db.query(Actor).filter_by(id=actor_id).first()
    commune = db.query(Commune).filter_by(id=commune_id).first()
    payload = {
        "v": 1,
        "type": "MADAVOLA_CARD",
        "card_type": card_type,
        "card_id": card.id,
        "card_number": card.card_number,
        "actor_id": actor_id,
        "full_name": f"{actor.nom} {actor.prenoms or ''}".strip() if actor else f"ACT-{actor_id}",
        "dob": actor.date_naissance.isoformat() if actor and actor.date_naissance else None,
        "filiere": filiere,
        "role": role,
        "commune_code": commune.code if commune else None,
        "status": _display_status(card.status),
        "validated_at": card.validated_at.isoformat() if card.validated_at else None,
        "expires_at": card.expires_at.isoformat() if card.expires_at else None,
    }
    canonical = canonical_json(payload)
    payload_hash = sha256_hex(canonical)
    signing_secret = settings.card_qr_signing_secret or settings.jwt_secret
    signature = sign_hmac_sha256(signing_secret, payload_hash)
    payload["qr_hash"] = payload_hash
    payload["sig"] = signature
    return payload


def _refresh_kara_qr(card: KaraBolamenaCard, db: Session) -> None:
    payload = _card_payload(
        db,
        card_type="kara_bolamena",
        card=card,
        actor_id=card.actor_id,
        commune_id=card.commune_id,
        role="orpailleur",
        filiere="OR",
    )
    card.qr_payload_json = canonical_json(payload)
    card.qr_payload_hash = payload["qr_hash"]
    card.qr_signature = payload["sig"]
    card.qr_value = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def _refresh_collector_qr(card: CollectorCard, db: Session) -> None:
    role = "bijoutier" if _is_bijoutier_card(card) else "collecteur"
    payload = _card_payload(
        db,
        card_type="collector_card",
        card=card,
        actor_id=card.actor_id,
        commune_id=card.issuing_commune_id,
        role=role,
        filiere="OR",
    )
    card.qr_payload_json = canonical_json(payload)
    card.qr_payload_hash = payload["qr_hash"]
    card.qr_signature = payload["sig"]
    card.qr_value = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def _ensure_card_documents(db: Session, card, card_type: str) -> None:
    actor = db.query(Actor).filter_by(id=card.actor_id).first()
    commune_id = card.commune_id if card_type == "kara_bolamena" else card.issuing_commune_id
    commune = db.query(Commune).filter_by(id=commune_id).first()
    full_name = f"{actor.nom} {actor.prenoms or ''}".strip() if actor else f"Acteur {card.actor_id}"
    status = _display_status(card.status)
    role_label = "Orpailleur" if card_type == "kara_bolamena" else ("Bijoutier" if _is_bijoutier_card(card) else "Collecteur")
    commune_label = commune.name if commune else f"Commune {commune_id}"
    qr_short = card.qr_payload_hash or "-"
    cin_raw = actor.cin if actor else None
    cin_digits = "".join(ch for ch in (cin_raw or "") if ch.isdigit())
    cin_display = " ".join([cin_digits[i:i + 3] for i in range(0, len(cin_digits), 3)]) if cin_digits else "-"
    date_naissance = actor.date_naissance.isoformat() if actor and actor.date_naissance else "-"
    cin_delivrance = actor.cin_date_delivrance.isoformat() if actor and actor.cin_date_delivrance else "-"
    adresse = actor.adresse_text if actor and actor.adresse_text else "-"
    verified_ref = card.card_number or str(card.id)

    front_lines = [
        f"Nom: {full_name}",
        f"Ne(e) le: {date_naissance}",
        f"Adresse: {adresse}",
        f"CIN: {cin_display}",
        f"Delivrance CIN: {cin_delivrance}",
        f"Carte: {card.card_number or '-'}",
        f"Role: {role_label} | Filiere: OR",
        f"Emission: {card.issued_at.isoformat() if card.issued_at else '-'}",
        f"Validite: {card.expires_at.isoformat() if card.expires_at else '-'}",
        f"Commune: {commune_label}",
    ]
    back_lines = [
        f"Numero carte: {card.card_number or '-'}",
        f"Card UID: {card.card_uid or '-'}",
        f"Statut: {status}",
        f"QR Hash: {qr_short}",
        f"Signature: {card.qr_signature or '-'}",
        f"Verification: {settings.api_prefix}/verify/card/{verified_ref}",
    ]
    # ISO/IEC 7810 ID-1 (85.60 x 53.98 mm) in PDF points.
    page_width_pt = 243
    page_height_pt = 153
    front_bytes = build_simple_pdf(
        "MADAVOLA - Carte OR",
        front_lines,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        start_x=10,
        start_y=140,
        line_height=10,
        font_size=8,
    )
    back_bytes = build_simple_pdf(
        "MADAVOLA - Verification",
        back_lines,
        page_width_pt=page_width_pt,
        page_height_pt=page_height_pt,
        start_x=10,
        start_y=140,
        line_height=10,
        font_size=8,
    )

    owner_actor_id = card.actor_id
    front_doc_id = _upsert_document_blob(
        db,
        existing_document_id=card.front_document_id,
        doc_type="card_front",
        owner_actor_id=owner_actor_id,
        related_entity_type="card",
        related_entity_id=f"{card_type}:{card.id}:front",
        filename=f"card-{card_type}-{card.id}-front.pdf",
        content=front_bytes,
    )
    back_doc_id = _upsert_document_blob(
        db,
        existing_document_id=card.back_document_id,
        doc_type="card_back",
        owner_actor_id=owner_actor_id,
        related_entity_type="card",
        related_entity_id=f"{card_type}:{card.id}:back",
        filename=f"card-{card_type}-{card.id}-back.pdf",
        content=back_bytes,
    )
    card.front_document_id = front_doc_id
    card.back_document_id = back_doc_id


def _upsert_document_blob(
    db: Session,
    *,
    existing_document_id: int | None,
    doc_type: str,
    owner_actor_id: int,
    related_entity_type: str,
    related_entity_id: str,
    filename: str,
    content: bytes,
) -> int:
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / filename
    path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    document = db.query(Document).filter_by(id=existing_document_id).first() if existing_document_id else None
    if not document:
        document = Document(
            doc_type=doc_type,
            owner_actor_id=owner_actor_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            storage_path=str(path),
            original_filename=filename,
            sha256=sha256,
        )
        db.add(document)
        db.flush()
        return int(document.id)
    document.doc_type = doc_type
    document.owner_actor_id = owner_actor_id
    document.related_entity_type = related_entity_type
    document.related_entity_id = related_entity_id
    document.storage_path = str(path)
    document.original_filename = filename
    document.sha256 = sha256
    return int(document.id)


def _is_active_commune(db: Session, commune_id: int | None) -> bool:
    if not commune_id:
        return False
    active = db.query(TerritoryVersion).filter_by(status="active").first()
    if not active:
        return False
    return (
        db.query(Commune.id)
        .filter(Commune.id == commune_id, Commune.version_id == active.id)
        .first()
        is not None
    )
