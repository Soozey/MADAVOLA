from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.card_identity import build_invoice_number, build_receipt_number
from app.common.errors import bad_request, conflict, not_found
from app.common.receipts import build_simple_pdf
from app.core.config import settings
from app.db import get_db
from app.models.admin import SystemConfig
from app.models.actor import ActorRole
from app.models.document import Document
from app.models.gold_ops import LegalVersioning, TaxBreakdown
from app.models.payment import PaymentRequest
from app.models.tax import LocalMarketValue, TaxEventRegistry, TaxRecord
from app.taxes.schemas import (
    CreateTaxEventIn,
    CreateTaxEventOut,
    LocalMarketValueCreateIn,
    LocalMarketValueOut,
    TaxBeneficiaryOut,
    TaxBreakdownOut,
    TaxComponentOut,
    TaxEventOut,
    TaxRecordOut,
    TaxStatusPatchIn,
)
from app.taxes.service import (
    EVENT_DROIT_CARTE_COLLECTEUR,
    EVENT_EXPORT_DTSPM,
    EVENT_LOCAL_SALE_DTSPM,
    compute_tax_event_breakdown,
    default_assiette_mode_for_event,
    default_legal_key_for_event,
    normalize_event_type,
)

router = APIRouter(prefix=f"{settings.api_prefix}/taxes", tags=["taxes"])


@router.get("/dtspm/breakdown", response_model=TaxBreakdownOut)
def preview_dtspm_breakdown(base_amount: float, currency: str = "MGA"):
    if base_amount <= 0:
        raise bad_request("base_imposition_invalide")
    breakdown = compute_tax_event_breakdown(
        event_type=EVENT_EXPORT_DTSPM,
        base_amount=Decimal(str(base_amount)),
        currency=currency.upper(),
        assiette_mode="manual",
        assiette_reference="preview",
    )
    return _to_breakdown_out(
        breakdown=breakdown,
        commune_beneficiary_id=None,
        region_beneficiary_id=None,
        province_beneficiary_id=None,
        province_note="a_attribuer",
        commune_rule_note=None,
    )


@router.post("/local-market-values", response_model=LocalMarketValueOut, status_code=201)
def create_local_market_value(
    payload: LocalMarketValueCreateIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "mmrs", "mef", "tresor", "com", "com_admin"})),
):
    if payload.effective_to and payload.effective_to <= payload.effective_from:
        raise bad_request("periode_legale_invalide")
    row = LocalMarketValue(
        filiere=payload.filiere.strip().upper(),
        substance=payload.substance.strip().upper(),
        region_code=(payload.region_code or "").strip().upper() or None,
        commune_code=(payload.commune_code or "").strip().upper() or None,
        unit=(payload.unit or "").strip().lower() or "kg",
        value_per_unit=payload.value_per_unit,
        currency=payload.currency.strip().upper(),
        legal_reference=payload.legal_reference.strip(),
        version_tag=payload.version_tag.strip(),
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status=payload.status,
        created_by_actor_id=current_actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_local_value_out(row)


@router.get("/local-market-values", response_model=list[LocalMarketValueOut])
def list_local_market_values(
    filiere: str | None = None,
    substance: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(LocalMarketValue)
    if filiere:
        query = query.filter(LocalMarketValue.filiere == filiere.strip().upper())
    if substance:
        query = query.filter(LocalMarketValue.substance == substance.strip().upper())
    if status:
        query = query.filter(LocalMarketValue.status == status.strip().lower())
    rows = query.order_by(LocalMarketValue.effective_from.desc(), LocalMarketValue.id.desc()).all()
    return [_to_local_value_out(row) for row in rows]


@router.get("/events", response_model=list[TaxEventOut])
def list_tax_events(
    taxable_event_type: str | None = None,
    status: str | None = None,
    lot_id: int | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(TaxEventRegistry)
    if taxable_event_type:
        query = query.filter(TaxEventRegistry.taxable_event_type == normalize_event_type(taxable_event_type))
    if status:
        query = query.filter(TaxEventRegistry.status == status.strip().upper())
    if lot_id is not None:
        query = query.filter(TaxEventRegistry.lot_id == lot_id)
    rows = query.order_by(TaxEventRegistry.created_at.desc(), TaxEventRegistry.id.desc()).all()
    return [_to_tax_event_out(row) for row in rows]


@router.get("/events/{event_registry_id}", response_model=TaxEventOut)
def get_tax_event(
    event_registry_id: int,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    row = db.query(TaxEventRegistry).filter(TaxEventRegistry.id == event_registry_id).first()
    if not row:
        raise not_found("evenement_fiscal_introuvable")
    return _to_tax_event_out(row)


@router.post(
    "/events",
    response_model=CreateTaxEventOut,
    status_code=201,
)
def create_taxes_for_event(
    payload: CreateTaxEventIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "tresor", "mef", "bfm", "com", "com_admin"})),
):
    normalized_event_type = normalize_event_type(payload.taxable_event_type)
    normalized_event_id = payload.taxable_event_id.strip()
    if not normalized_event_id:
        raise bad_request("evenement_taxable_invalide")

    assiette_mode = (payload.assiette_mode or default_assiette_mode_for_event(normalized_event_type)).strip().lower()
    base_amount, assiette_reference = _resolve_base_amount_and_reference(
        db,
        payload=payload,
        normalized_event_type=normalized_event_type,
        assiette_mode=assiette_mode,
    )
    period_key = (payload.period_key or datetime.now(timezone.utc).strftime("%Y-%m")).strip()
    reference_transaction = (payload.reference_transaction or normalized_event_id).strip()
    anti_double_key = _build_anti_double_key(
        event_type=normalized_event_type,
        lot_id=payload.lot_id,
        period_key=period_key,
        reference_transaction=reference_transaction,
    )

    existing_registry = (
        db.query(TaxEventRegistry.id)
        .filter(
            TaxEventRegistry.anti_double_key == anti_double_key,
            TaxEventRegistry.status.in_(["DUE", "PAID"]),
        )
        .first()
    )
    if existing_registry:
        raise conflict("taxation_deja_existante_pour_evenement")

    existing_lines = (
        db.query(TaxRecord.id)
        .filter(TaxRecord.taxable_event_type == normalized_event_type)
        .filter(TaxRecord.taxable_event_id == normalized_event_id)
        .filter(TaxRecord.status.in_(["DUE", "PAID"]))
        .first()
    )
    if existing_lines:
        raise conflict("taxation_deja_existante_pour_evenement")

    if payload.unpaid_upstream_dtspm and normalized_event_type == EVENT_LOCAL_SALE_DTSPM:
        _assert_local_sale_liability_actor(db, payload.payer_actor_id, payload.payer_role_code)

    legal_key = (payload.legal_key or default_legal_key_for_event(normalized_event_type)).strip().lower()
    legal_version = (
        db.query(LegalVersioning)
        .filter(
            LegalVersioning.filiere == payload.filiere.strip().upper(),
            LegalVersioning.legal_key == legal_key,
            LegalVersioning.status == "active",
            LegalVersioning.effective_from <= datetime.now(timezone.utc),
        )
        .order_by(LegalVersioning.effective_from.desc())
        .first()
    )

    breakdown = compute_tax_event_breakdown(
        event_type=normalized_event_type,
        base_amount=base_amount,
        currency=payload.currency.upper(),
        filiere=payload.filiere.strip().upper(),
        assiette_mode=assiette_mode,
        assiette_reference=assiette_reference,
        legal_rule_payload_json=legal_version.payload_json if legal_version else None,
        is_transformed=bool(payload.transformed),
        transformation_origin=payload.transformation_origin,
    )
    breakdown_out = _to_breakdown_out(
        breakdown=breakdown,
        commune_beneficiary_id=payload.commune_beneficiary_id,
        region_beneficiary_id=payload.region_beneficiary_id,
        province_beneficiary_id=payload.province_beneficiary_id,
        province_note="a_attribuer" if payload.province_beneficiary_id is None else None,
        commune_rule_note=_get_commune_rule_note(db),
    )

    event_total = _breakdown_total_amount_decimal(breakdown)
    event = TaxEventRegistry(
        taxable_event_type=normalized_event_type,
        taxable_event_id=normalized_event_id,
        anti_double_key=anti_double_key,
        period_key=period_key,
        reference_transaction=reference_transaction,
        filiere=payload.filiere.strip().upper(),
        region_code=(payload.region_code or "").strip().upper() or None,
        assiette_mode=assiette_mode,
        assiette_reference=assiette_reference,
        base_amount=base_amount,
        currency=payload.currency.upper(),
        total_amount=event_total,
        abatement_rate=breakdown.get("abatement_rate") or Decimal("0"),
        abatement_reason=breakdown.get("abatement_reason"),
        legal_basis_json=json.dumps(breakdown.get("legal_basis", []), ensure_ascii=True),
        legal_version_id=legal_version.id if legal_version else None,
        payer_actor_id=payload.payer_actor_id,
        payer_role_code=(payload.payer_role_code or "").strip().lower() or None,
        lot_id=payload.lot_id,
        export_id=payload.export_id,
        transaction_id=payload.transaction_id,
        status="DUE",
        created_by_actor_id=current_actor.id,
    )
    db.add(event)
    db.flush()
    event.invoice_number = build_invoice_number(
        event.id,
        filiere=event.filiere,
        region_code=event.region_code,
        now=datetime.now(timezone.utc),
    )
    _ensure_tax_event_invoice_document(db, event=event, breakdown=breakdown)

    records: list[TaxRecord] = []
    tax_breakdown_rows: list[TaxBreakdown] = []
    for component in breakdown_out.components:
        for beneficiary in component.beneficiaries:
            records.append(
                TaxRecord(
                    taxable_event_type=normalized_event_type,
                    taxable_event_id=normalized_event_id,
                    tax_type=component.tax_type,
                    beneficiary_level=beneficiary.beneficiary_level,
                    beneficiary_id=beneficiary.beneficiary_id,
                    beneficiary_key=_beneficiary_key(beneficiary.beneficiary_id),
                    base_amount=base_amount,
                    tax_rate=beneficiary.rate_of_base,
                    tax_amount=beneficiary.amount,
                    currency=payload.currency.upper(),
                    lot_id=payload.lot_id,
                    export_id=payload.export_id,
                    transaction_id=payload.transaction_id,
                    status="DUE",
                    attribution_note=beneficiary.attribution_note,
                    created_by_actor_id=current_actor.id,
                )
            )
            tax_breakdown_rows.append(
                TaxBreakdown(
                    taxable_event_type=normalized_event_type,
                    taxable_event_id=normalized_event_id,
                    legal_version_id=legal_version.id if legal_version else None,
                    tax_type=component.tax_type,
                    beneficiary_level=beneficiary.beneficiary_level,
                    beneficiary_id=beneficiary.beneficiary_id,
                    base_amount=base_amount,
                    tax_rate=beneficiary.rate_of_base,
                    tax_amount=beneficiary.amount,
                    currency=payload.currency.upper(),
                    status="DUE",
                )
            )
    db.add_all(records)
    db.add_all(tax_breakdown_rows)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("taxation_deja_existante_pour_evenement")

    return CreateTaxEventOut(
        event=_to_tax_event_out(event),
        breakdown=breakdown_out,
        records=[_to_record_out(item) for item in records],
    )


@router.get("", response_model=list[TaxRecordOut])
def list_taxes(
    taxable_event_type: str | None = None,
    taxable_event_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(TaxRecord)
    if taxable_event_type:
        query = query.filter(TaxRecord.taxable_event_type == normalize_event_type(taxable_event_type))
    if taxable_event_id:
        query = query.filter(TaxRecord.taxable_event_id == taxable_event_id.strip())
    if status:
        query = query.filter(TaxRecord.status == status.upper())
    rows = query.order_by(TaxRecord.id.asc()).all()
    return [_to_record_out(item) for item in rows]


@router.patch("/{tax_id}/status", response_model=TaxRecordOut)
def update_tax_status(
    tax_id: int,
    payload: TaxStatusPatchIn,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "tresor", "mef", "bfm", "com", "com_admin"})),
):
    row = db.query(TaxRecord).filter(TaxRecord.id == tax_id).first()
    if not row:
        raise not_found("taxe_introuvable")
    next_status = payload.status.upper()
    if next_status == "PAID":
        if not payload.payment_request_id:
            raise bad_request("preuve_paiement_obligatoire")
        payment = db.query(PaymentRequest).filter(PaymentRequest.id == payload.payment_request_id).first()
        if not payment or payment.status != "success":
            raise bad_request("paiement_non_confirme")
        if Decimal(str(payment.amount)) < Decimal(str(row.tax_amount)):
            raise bad_request("montant_paiement_insuffisant")

    row.status = next_status
    db.add(row)
    breakdown_rows = (
        db.query(TaxBreakdown)
        .filter(
            TaxBreakdown.taxable_event_type == row.taxable_event_type,
            TaxBreakdown.taxable_event_id == row.taxable_event_id,
            TaxBreakdown.tax_type == row.tax_type,
            TaxBreakdown.beneficiary_level == row.beneficiary_level,
        )
        .all()
    )
    for item in breakdown_rows:
        item.status = next_status
        if payload.payment_request_id:
            item.payment_request_id = payload.payment_request_id
        db.add(item)
    db.flush()

    _sync_tax_event_registry_status(
        db,
        taxable_event_type=row.taxable_event_type,
        taxable_event_id=row.taxable_event_id,
        payment_request_id=payload.payment_request_id if next_status == "PAID" else None,
    )
    db.commit()
    db.refresh(row)
    return _to_record_out(row)


def _resolve_base_amount_and_reference(
    db: Session,
    *,
    payload: CreateTaxEventIn,
    normalized_event_type: str,
    assiette_mode: str,
) -> tuple[Decimal, str | None]:
    if assiette_mode == "local_market_value":
        if payload.base_amount is not None:
            return Decimal(str(payload.base_amount)), "LOCAL_MARKET_VALUE_OVERRIDE_BASE"
        if payload.quantity is None:
            raise bad_request("quantite_locale_obligatoire")
        if payload.local_market_value_override is not None:
            base = Decimal(str(payload.quantity)) * Decimal(str(payload.local_market_value_override))
            return base.quantize(Decimal("0.01")), "LOCAL_MARKET_VALUE_OVERRIDE"
        row = _find_active_local_market_value(
            db,
            filiere=payload.filiere,
            substance=payload.substance,
            region_code=payload.region_code,
        )
        if not row:
            raise bad_request("valeur_marchande_locale_introuvable")
        base = Decimal(str(payload.quantity)) * Decimal(str(row.value_per_unit))
        return base.quantize(Decimal("0.01")), f"LOCAL_MARKET_VALUE:{row.id}:{row.version_tag}"

    if payload.base_amount is None:
        raise bad_request("base_imposition_obligatoire")
    reference = "MANUAL"
    if assiette_mode == "fob_export":
        reference = "FOB_EXPORT_DECLARED"
    elif assiette_mode == "fixed_amount":
        reference = "FIXED_AMOUNT_DECLARED"
    elif normalized_event_type == EVENT_EXPORT_DTSPM:
        reference = "FOB_EXPORT_DECLARED"
    return Decimal(str(payload.base_amount)), reference


def _find_active_local_market_value(
    db: Session,
    *,
    filiere: str,
    substance: str | None,
    region_code: str | None,
) -> LocalMarketValue | None:
    now = datetime.now(timezone.utc)
    target_filiere = (filiere or "OR").strip().upper()
    target_substance = (substance or target_filiere).strip().upper()
    rows = (
        db.query(LocalMarketValue)
        .filter(
            LocalMarketValue.filiere == target_filiere,
            LocalMarketValue.substance == target_substance,
            LocalMarketValue.status == "active",
            LocalMarketValue.effective_from <= now,
        )
        .order_by(LocalMarketValue.effective_from.desc(), LocalMarketValue.id.desc())
        .all()
    )
    filtered: list[LocalMarketValue] = []
    for row in rows:
        if row.effective_to is None:
            filtered.append(row)
            continue
        effective_to = row.effective_to
        if effective_to.tzinfo is None:
            effective_to = effective_to.replace(tzinfo=timezone.utc)
        if effective_to >= now:
            filtered.append(row)
    if not filtered:
        return None
    target_region = (region_code or "").strip().upper()
    if target_region:
        exact_region = [row for row in filtered if (row.region_code or "").strip().upper() == target_region]
        if exact_region:
            return exact_region[0]
    return filtered[0]


def _build_anti_double_key(
    *,
    event_type: str,
    lot_id: int | None,
    period_key: str,
    reference_transaction: str,
) -> str:
    raw = f"{event_type}|{lot_id or '-'}|{period_key}|{reference_transaction}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _assert_local_sale_liability_actor(db: Session, payer_actor_id: int | None, payer_role_code: str | None) -> None:
    allowed = {"comptoir_operator", "comptoir_compliance", "comptoir_director", "bijoutier"}
    if payer_role_code and payer_role_code.strip().lower() in allowed:
        return
    if not payer_actor_id:
        raise bad_request("responsable_paiement_local_obligatoire")
    role = (
        db.query(ActorRole.id)
        .filter(
            ActorRole.actor_id == payer_actor_id,
            ActorRole.status == "active",
            ActorRole.role.in_(sorted(allowed)),
        )
        .all()
    )
    if not role:
        raise bad_request("responsable_paiement_local_invalide")


def _sync_tax_event_registry_status(
    db: Session,
    *,
    taxable_event_type: str,
    taxable_event_id: str,
    payment_request_id: int | None,
) -> None:
    registry = (
        db.query(TaxEventRegistry)
        .filter(
            TaxEventRegistry.taxable_event_type == taxable_event_type,
            TaxEventRegistry.taxable_event_id == taxable_event_id,
        )
        .order_by(TaxEventRegistry.id.desc())
        .first()
    )
    if not registry:
        return
    statuses = (
        db.query(TaxRecord.status)
        .filter(
            TaxRecord.taxable_event_type == taxable_event_type,
            TaxRecord.taxable_event_id == taxable_event_id,
        )
        .all()
    )
    status_set = {row[0] for row in statuses}
    if status_set and status_set == {"PAID"}:
        registry.status = "PAID"
        if payment_request_id:
            registry.payment_request_id = payment_request_id
        _ensure_tax_event_receipt_document(db, registry)
    elif status_set and status_set == {"VOID"}:
        registry.status = "VOID"
    else:
        registry.status = "DUE"
    db.add(registry)


def _ensure_tax_event_invoice_document(db: Session, *, event: TaxEventRegistry, breakdown: dict) -> None:
    if event.invoice_document_id and event.invoice_number:
        return
    lines = [
        f"Facture: {event.invoice_number}",
        f"Evenement fiscal: {event.taxable_event_type}",
        f"Reference evenement: {event.taxable_event_id}",
        f"Filiere: {event.filiere}",
        f"Assiette mode: {event.assiette_mode}",
        f"Assiette reference: {event.assiette_reference or '-'}",
        f"Base: {float(event.base_amount):.2f} {event.currency}",
        f"Total fiscal: {float(event.total_amount):.2f} {event.currency}",
        f"Abattement: {float(event.abatement_rate) * 100:.2f}%",
        f"Statut: {event.status}",
    ]
    for component in breakdown.get("components", []):
        lines.append(f"{component['tax_type']}: {float(component['amount']):.2f} {event.currency}")
        for beneficiary in component.get("beneficiaries", []):
            lines.append(
                f" - {beneficiary['beneficiary_level']} ({float(beneficiary['allocation_share']) * 100:.2f}%): {float(beneficiary['amount']):.2f} {event.currency}"
            )
    for ref in breakdown.get("legal_basis", []):
        lines.append(f"Base legale: {ref}")
    content = build_simple_pdf("MADAVOLA - Facture evenement fiscal", lines)
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{event.invoice_number}.pdf"
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)
    doc = Document(
        doc_type="invoice",
        owner_actor_id=event.payer_actor_id or event.created_by_actor_id or 0,
        related_entity_type="tax_event",
        related_entity_id=str(event.id),
        storage_path=str(storage_path),
        original_filename=filename,
        sha256=hashlib.sha256(content).hexdigest(),
    )
    db.add(doc)
    db.flush()
    event.invoice_document_id = doc.id


def _ensure_tax_event_receipt_document(db: Session, event: TaxEventRegistry) -> None:
    if event.receipt_document_id and event.receipt_number:
        return
    now = datetime.now(timezone.utc)
    event.receipt_number = build_receipt_number(event.id, now=now)
    lines = [
        f"Recu: {event.receipt_number}",
        f"Facture: {event.invoice_number or '-'}",
        f"Evenement fiscal: {event.taxable_event_type}",
        f"Reference evenement: {event.taxable_event_id}",
        f"Montant total: {float(event.total_amount):.2f} {event.currency}",
        f"Paiement ref: {event.payment_request_id or '-'}",
        f"Date: {now.isoformat()}",
    ]
    for ref in _parse_json_list(event.legal_basis_json):
        lines.append(f"Base legale: {ref}")
    content = build_simple_pdf("MADAVOLA - Recu evenement fiscal", lines)
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{event.receipt_number}.pdf"
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)
    doc = Document(
        doc_type="receipt",
        owner_actor_id=event.payer_actor_id or event.created_by_actor_id or 0,
        related_entity_type="tax_event",
        related_entity_id=str(event.id),
        storage_path=str(storage_path),
        original_filename=filename,
        sha256=hashlib.sha256(content).hexdigest(),
    )
    db.add(doc)
    db.flush()
    event.receipt_document_id = doc.id


def _beneficiary_key(beneficiary_id: int | None) -> str:
    return str(beneficiary_id) if beneficiary_id is not None else "__NONE__"


def _get_commune_rule_note(db: Session) -> str:
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "dtspm_commune_distribution_rule").first()
    if cfg and cfg.value and cfg.value.strip():
        return cfg.value.strip()
    return "placeholder_reglementaire_communes_concernees_vs_impactees"


def _to_breakdown_out(
    *,
    breakdown: dict,
    commune_beneficiary_id: int | None,
    region_beneficiary_id: int | None,
    province_beneficiary_id: int | None,
    province_note: str | None,
    commune_rule_note: str | None,
) -> TaxBreakdownOut:
    components: list[TaxComponentOut] = []
    redevance_component: TaxComponentOut | None = None
    ristourne_component: TaxComponentOut | None = None

    for raw_component in breakdown.get("components", []):
        beneficiaries: list[TaxBeneficiaryOut] = []
        for raw in raw_component.get("beneficiaries", []):
            level = str(raw.get("beneficiary_level", "")).upper()
            beneficiary_id = None
            note = None
            if level == "COMMUNE":
                beneficiary_id = commune_beneficiary_id
                note = commune_rule_note
            elif level == "REGION":
                beneficiary_id = region_beneficiary_id
            elif level == "PROVINCE":
                beneficiary_id = province_beneficiary_id
                note = province_note
            beneficiaries.append(
                TaxBeneficiaryOut(
                    beneficiary_level=level,
                    beneficiary_id=beneficiary_id,
                    allocation_share=float(raw.get("allocation_share", 0)),
                    rate_of_base=float(raw.get("rate_of_base", 0)),
                    amount=float(raw.get("amount", 0)),
                    attribution_note=note,
                )
            )
        component_out = TaxComponentOut(
            tax_type=str(raw_component.get("tax_type")),
            rate=float(raw_component.get("rate", 0)),
            amount=float(raw_component.get("amount", 0)),
            beneficiaries=beneficiaries,
        )
        components.append(component_out)
        if component_out.tax_type == "DTSPM_REDEVANCE":
            redevance_component = component_out
        if component_out.tax_type == "DTSPM_RISTOURNE":
            ristourne_component = component_out

    return TaxBreakdownOut(
        event_type=str(breakdown.get("event_type")),
        base_amount=float(breakdown.get("base_amount", 0)),
        currency=str(breakdown.get("currency", "MGA")),
        assiette_mode=str(breakdown.get("assiette_mode", "manual")),
        assiette_reference=breakdown.get("assiette_reference"),
        dtspm_total_rate=float(breakdown["dtspm_total_rate"]) if breakdown.get("dtspm_total_rate") is not None else None,
        dtspm_total_amount=float(breakdown["dtspm_total_amount"]) if breakdown.get("dtspm_total_amount") is not None else None,
        abatement_rate=float(breakdown["abatement_rate"]) if breakdown.get("abatement_rate") is not None else None,
        abatement_reason=breakdown.get("abatement_reason"),
        legal_basis=[str(x) for x in breakdown.get("legal_basis", [])],
        redevance=redevance_component,
        ristourne=ristourne_component,
        components=components,
    )


def _to_record_out(row: TaxRecord) -> TaxRecordOut:
    return TaxRecordOut(
        id=row.id,
        taxable_event_type=row.taxable_event_type,
        taxable_event_id=row.taxable_event_id,
        tax_type=row.tax_type,
        beneficiary_level=row.beneficiary_level,
        beneficiary_id=row.beneficiary_id,
        base_amount=float(row.base_amount),
        tax_rate=float(row.tax_rate),
        tax_amount=float(row.tax_amount),
        currency=row.currency,
        lot_id=row.lot_id,
        export_id=row.export_id,
        transaction_id=row.transaction_id,
        status=row.status,
        attribution_note=row.attribution_note,
    )


def _to_local_value_out(row: LocalMarketValue) -> LocalMarketValueOut:
    return LocalMarketValueOut(
        id=row.id,
        filiere=row.filiere,
        substance=row.substance,
        region_code=row.region_code,
        commune_code=row.commune_code,
        unit=row.unit,
        value_per_unit=float(row.value_per_unit),
        currency=row.currency,
        legal_reference=row.legal_reference,
        version_tag=row.version_tag,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        status=row.status,
    )


def _to_tax_event_out(row: TaxEventRegistry) -> TaxEventOut:
    return TaxEventOut(
        id=row.id,
        taxable_event_type=row.taxable_event_type,
        taxable_event_id=row.taxable_event_id,
        anti_double_key=row.anti_double_key,
        period_key=row.period_key,
        reference_transaction=row.reference_transaction,
        filiere=row.filiere,
        region_code=row.region_code,
        assiette_mode=row.assiette_mode,
        assiette_reference=row.assiette_reference,
        base_amount=float(row.base_amount),
        currency=row.currency,
        total_amount=float(row.total_amount),
        abatement_rate=float(row.abatement_rate),
        abatement_reason=row.abatement_reason,
        legal_basis=_parse_json_list(row.legal_basis_json),
        legal_version_id=row.legal_version_id,
        payer_actor_id=row.payer_actor_id,
        payer_role_code=row.payer_role_code,
        lot_id=row.lot_id,
        export_id=row.export_id,
        transaction_id=row.transaction_id,
        status=row.status,
        invoice_number=row.invoice_number,
        invoice_document_id=row.invoice_document_id,
        receipt_number=row.receipt_number,
        receipt_document_id=row.receipt_document_id,
        payment_request_id=row.payment_request_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, list):
            return [str(x) for x in loaded]
    except Exception:
        return []
    return []


def _breakdown_total_amount_decimal(breakdown: dict) -> Decimal:
    if breakdown.get("dtspm_total_amount") is not None:
        return Decimal(str(breakdown["dtspm_total_amount"]))
    total = Decimal("0")
    for component in breakdown.get("components", []):
        total += Decimal(str(component.get("amount", 0)))
    return total
