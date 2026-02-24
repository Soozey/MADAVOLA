from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.logger import write_audit
from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
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
        unique_identifier=card.unique_identifier,
        status=card.status,
        cin=card.cin,
        nationality=card.nationality,
        residence_verified=card.residence_verified,
        tax_compliant=card.tax_compliant,
        zone_allowed=card.zone_allowed,
        public_order_clear=card.public_order_clear,
        fee_id=card.fee_id,
        issued_at=card.issued_at,
        expires_at=card.expires_at,
    )


def _to_collector_out(card: CollectorCard) -> CollectorCardOut:
    return CollectorCardOut(
        id=card.id,
        actor_id=card.actor_id,
        issuing_commune_id=card.issuing_commune_id,
        status=card.status,
        fee_id=card.fee_id,
        issued_at=card.issued_at,
        expires_at=card.expires_at,
        affiliation_deadline_at=card.affiliation_deadline_at,
        affiliation_submitted_at=card.affiliation_submitted_at,
        laissez_passer_blocked_reason=card.laissez_passer_blocked_reason,
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

    card = KaraBolamenaCard(
        actor_id=payload.actor_id,
        commune_id=payload.commune_id,
        unique_identifier=f"KARA-{now.strftime('%Y%m%d')}-{payload.actor_id}-{fee.id}",
        status="pending",
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
        query = query.filter(KaraBolamenaCard.status == status)
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
    if decision not in {"approved", "rejected", "suspended", "withdrawn"}:
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
        card.status = "active"
        card.issued_by_actor_id = current_actor.id
        card.issued_at = now
        card.expires_at = now + timedelta(days=365)
    else:
        card.status = "rejected" if decision == "rejected" else decision
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
    if card.status != "active":
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
    card = CollectorCard(
        actor_id=payload.actor_id,
        issuing_commune_id=payload.issuing_commune_id,
        status="pending",
        fee_id=fee.id,
        laissez_passer_blocked_reason="affiliation_non_communiquee",
    )
    db.add(card)
    db.flush()
    for doc_type in COLLECTOR_REQUIRED_DOCS:
        db.add(
            CollectorCardDocument(
                collector_card_id=card.id,
                doc_type=doc_type,
                required=True,
                status="uploaded",
                notes="declaration_initiale_acteur",
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
        query = query.filter(CollectorCard.status == status)
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
    if decision not in {"approved", "rejected", "suspended", "withdrawn"}:
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
        card.status = "active"
        card.issued_by_actor_id = current_actor.id
        card.issued_at = now
        card.expires_at = now + timedelta(days=365)
        card.affiliation_deadline_at = now + timedelta(days=90)
    else:
        card.status = "rejected" if decision == "rejected" else decision
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
    status: str = "pending",
    commune_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune", "commune_agent", "com", "com_admin", "com_agent"})),
):
    target_commune = commune_id or current_actor.commune_id
    if not target_commune and current_actor.id:
        raise bad_request("commune_invalide")
    if target_commune and not _is_active_commune(db, target_commune):
        raise bad_request("commune_invalide")

    kara_rows = (
        db.query(KaraBolamenaCard, Fee, Actor)
        .join(Fee, Fee.id == KaraBolamenaCard.fee_id, isouter=True)
        .join(Actor, Actor.id == KaraBolamenaCard.actor_id)
        .filter(KaraBolamenaCard.commune_id == target_commune, KaraBolamenaCard.status == status)
        .all()
    )
    collector_rows = (
        db.query(CollectorCard, Fee, Actor)
        .join(Fee, Fee.id == CollectorCard.fee_id, isouter=True)
        .join(Actor, Actor.id == CollectorCard.actor_id)
        .filter(CollectorCard.issuing_commune_id == target_commune, CollectorCard.status == status)
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
                status=card.status,
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
                status=card.status,
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
