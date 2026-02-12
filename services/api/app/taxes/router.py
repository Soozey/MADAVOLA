from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request, conflict, not_found
from app.core.config import settings
from app.db import get_db
from app.models.admin import SystemConfig
from app.models.tax import TaxRecord
from app.taxes.schemas import (
    CreateTaxEventIn,
    CreateTaxEventOut,
    TaxBeneficiaryOut,
    TaxBreakdownOut,
    TaxComponentOut,
    TaxRecordOut,
    TaxStatusPatchIn,
)
from app.taxes.service import compute_dtspm_breakdown

router = APIRouter(prefix=f"{settings.api_prefix}/taxes", tags=["taxes"])


@router.get("/dtspm/breakdown", response_model=TaxBreakdownOut)
def preview_dtspm_breakdown(base_amount: float, currency: str = "MGA"):
    if base_amount <= 0:
        raise bad_request("base_imposition_invalide")
    breakdown = compute_dtspm_breakdown(Decimal(str(base_amount)), currency.upper())
    return _to_breakdown_out(
        breakdown=breakdown,
        commune_beneficiary_id=None,
        region_beneficiary_id=None,
        province_beneficiary_id=None,
        province_note="a_attribuer",
        commune_rule_note=None,
    )


@router.post(
    "/events",
    response_model=CreateTaxEventOut,
    status_code=201,
)
def create_taxes_for_event(
    payload: CreateTaxEventIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "tresor", "mef", "bfm"})),
):
    normalized_event_type = payload.taxable_event_type.strip().lower()
    normalized_event_id = payload.taxable_event_id.strip()
    if not normalized_event_id:
        raise bad_request("evenement_taxable_invalide")

    existing = (
        db.query(TaxRecord.id)
        .filter(TaxRecord.taxable_event_type == normalized_event_type)
        .filter(TaxRecord.taxable_event_id == normalized_event_id)
        .filter(TaxRecord.status.in_(["DUE", "PAID"]))
        .first()
    )
    if existing:
        raise conflict("taxation_deja_existante_pour_evenement")

    breakdown = compute_dtspm_breakdown(
        Decimal(str(payload.base_amount)),
        payload.currency.upper(),
    )
    commune_rule_note = _get_commune_rule_note(db)
    province_note = "a_attribuer" if payload.province_beneficiary_id is None else None
    breakdown_out = _to_breakdown_out(
        breakdown=breakdown,
        commune_beneficiary_id=payload.commune_beneficiary_id,
        region_beneficiary_id=payload.region_beneficiary_id,
        province_beneficiary_id=payload.province_beneficiary_id,
        province_note=province_note,
        commune_rule_note=commune_rule_note,
    )

    records: list[TaxRecord] = []
    for beneficiary in breakdown_out.redevance.beneficiaries:
        records.append(
            TaxRecord(
                taxable_event_type=normalized_event_type,
                taxable_event_id=normalized_event_id,
                tax_type=breakdown_out.redevance.tax_type,
                beneficiary_level=beneficiary.beneficiary_level,
                beneficiary_id=beneficiary.beneficiary_id,
                beneficiary_key=_beneficiary_key(beneficiary.beneficiary_id),
                base_amount=payload.base_amount,
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
    for beneficiary in breakdown_out.ristourne.beneficiaries:
        records.append(
            TaxRecord(
                taxable_event_type=normalized_event_type,
                taxable_event_id=normalized_event_id,
                tax_type=breakdown_out.ristourne.tax_type,
                beneficiary_level=beneficiary.beneficiary_level,
                beneficiary_id=beneficiary.beneficiary_id,
                beneficiary_key=_beneficiary_key(beneficiary.beneficiary_id),
                base_amount=payload.base_amount,
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

    db.add_all(records)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("taxation_deja_existante_pour_evenement")

    return CreateTaxEventOut(
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
        query = query.filter(TaxRecord.taxable_event_type == taxable_event_type.strip().lower())
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
    _actor=Depends(require_roles({"admin", "dirigeant", "tresor", "mef", "bfm"})),
):
    row = db.query(TaxRecord).filter(TaxRecord.id == tax_id).first()
    if not row:
        raise not_found("taxe_introuvable")
    row.status = payload.status.upper()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_record_out(row)


def _beneficiary_key(beneficiary_id: int | None) -> str:
    return str(beneficiary_id) if beneficiary_id is not None else "__NONE__"


def _get_commune_rule_note(db: Session) -> str:
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "dtspm_commune_distribution_rule").first()
    if cfg and cfg.value and cfg.value.strip():
        return cfg.value.strip()
    return "placeholder_reglementaire_communes_concernees_vs_impactees"


def _to_breakdown_out(
    breakdown: dict,
    commune_beneficiary_id: int | None,
    region_beneficiary_id: int | None,
    province_beneficiary_id: int | None,
    province_note: str | None,
    commune_rule_note: str | None,
) -> TaxBreakdownOut:
    redevance_beneficiaries = [
        TaxBeneficiaryOut(
            beneficiary_level="ETAT",
            beneficiary_id=None,
            allocation_share=float(breakdown["redevance"]["beneficiaries"][0]["allocation_share"]),
            rate_of_base=float(breakdown["redevance"]["beneficiaries"][0]["rate_of_base"]),
            amount=float(breakdown["redevance"]["beneficiaries"][0]["amount"]),
        )
    ]

    ristourne_beneficiaries: list[TaxBeneficiaryOut] = []
    for raw in breakdown["ristourne"]["beneficiaries"]:
        level = raw["beneficiary_level"]
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
        ristourne_beneficiaries.append(
            TaxBeneficiaryOut(
                beneficiary_level=level,
                beneficiary_id=beneficiary_id,
                allocation_share=float(raw["allocation_share"]),
                rate_of_base=float(raw["rate_of_base"]),
                amount=float(raw["amount"]),
                attribution_note=note,
            )
        )

    return TaxBreakdownOut(
        base_amount=float(breakdown["base_amount"]),
        currency=str(breakdown["currency"]),
        dtspm_total_rate=float(breakdown["dtspm_total_rate"]),
        dtspm_total_amount=float(breakdown["dtspm_total_amount"]),
        redevance=TaxComponentOut(
            tax_type=breakdown["redevance"]["tax_type"],
            rate=float(breakdown["redevance"]["rate"]),
            amount=float(breakdown["redevance"]["amount"]),
            beneficiaries=redevance_beneficiaries,
        ),
        ristourne=TaxComponentOut(
            tax_type=breakdown["ristourne"]["tax_type"],
            rate=float(breakdown["ristourne"]["rate"]),
            amount=float(breakdown["ristourne"]["amount"]),
            beneficiaries=ristourne_beneficiaries,
        ),
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
