from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.common.receipts import build_qr_value
from app.core.config import settings
from app.db import get_db
from app.exports.schemas import ExportCreate, ExportOut, ExportStatusUpdate, ExportLotLink
from app.models.export import ExportDossier, ExportLot
from app.models.gold_ops import ExportChecklistItem, ExportValidation, ForexRepatriation, LotTestCertificate
from app.models.actor import Actor, ActorRole
from app.models.lot import Lot
from app.models.tax import TaxRecord
from app.models.pierre import ActorAuthorization, ExportSeal, ExportValidationStep
from app.models.bois import EssenceCatalog, WorkflowApproval
from app.models.territory import Commune, TerritoryVersion

router = APIRouter(prefix=f"{settings.api_prefix}/exports", tags=["exports"])

EXPORT_ROLES = {
    "admin",
    "dirigeant",
    "commune_agent",
    "acteur",
    "orpailleur",
    "comptoir_operator",
    "comptoir_compliance",
    "comptoir_director",
    "bijoutier",
    "com",
    "gue",
    "analyse_certification",
    "pierre_exportateur",
    "pierre_controleur_mines",
    "pierre_douanes",
    "pierre_admin_central",
    "bois_exportateur",
    "bois_douanes",
    "bois_admin_central",
    "forets",
}

EXPORT_APPROVERS = {"admin", "dirigeant", "com", "gue"}
EXPORT_REQUIRED_DOC_TYPES = (
    "agrement_comptoir",
    "piece_origine",
    "contrat_import_export",
    "fiche_signaletique",
    "declaration_export",
    "facture_proforma",
    "laissez_passer",
)
CANONICAL_EXPORT_STEPS = [
    "production_declared",
    "collector_purchase",
    "counter_sale",
    "tested_certified",
    "refined_optional",
    "export_consolidated",
    "dtspm_paid",
    "com_validated",
    "customs_controlled",
    "exported",
    "forex_repatriated",
    "closed",
]


class ExportSubmitIn(BaseModel):
    status: str = "submitted"


class ExportValidateIn(BaseModel):
    step_code: str  # mines|douanes
    decision: str  # approved|rejected
    notes: str | None = None
    seal_number: str | None = None
    pv_document_id: int | None = None


def _is_admin(db: Session, actor_id: int) -> bool:
    role = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == "admin")
        .filter(ActorRole.status == "active")
        .first()
    )
    return role is not None


def _is_dirigeant(db: Session, actor_id: int) -> bool:
    role = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == "dirigeant")
        .filter(ActorRole.status == "active")
        .first()
    )
    return role is not None


def _is_commune_agent(db: Session, actor_id: int) -> bool:
    role = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == "commune_agent")
        .filter(ActorRole.status == "active")
        .first()
    )
    return role is not None


def _has_any_role(db: Session, actor_id: int, roles: set[str]) -> bool:
    role = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(roles), ActorRole.status == "active")
        .first()
    )
    return role is not None


def _can_access_export(db: Session, current_actor: Actor, export: ExportDossier) -> bool:
    if _is_admin(db, current_actor.id) or _is_dirigeant(db, current_actor.id):
        return True
    if _has_any_role(db, current_actor.id, {"com", "gue", "analyse_certification"}):
        return True
    if _is_commune_agent(db, current_actor.id):
        creator = db.query(Actor).filter_by(id=export.created_by_actor_id).first()
        if creator and creator.commune_id == current_actor.commune_id:
            return True
    if export.created_by_actor_id == current_actor.id:
        return True
    return False


def _active_roles(db: Session, actor_id: int) -> set[str]:
    rows = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    return {row[0] for row in rows}


def _ensure_active_authorization(db: Session, actor_id: int, filiere: str) -> None:
    now = datetime.now(timezone.utc)
    auth = (
        db.query(ActorAuthorization.id)
        .filter(
            ActorAuthorization.actor_id == actor_id,
            ActorAuthorization.filiere == filiere,
            ActorAuthorization.status == "active",
            ActorAuthorization.valid_from <= now,
            ActorAuthorization.valid_to >= now,
        )
        .first()
    )
    if not auth:
        raise bad_request("autorisation_expiree")


def _assert_creator_allowed_for_export(db: Session, actor_id: int) -> None:
    roles = _active_roles(db, actor_id)
    if "orpailleur" in roles and roles.isdisjoint({"collecteur", "comptoir_operator", "comptoir_compliance", "comptoir_director", "bijoutier", "admin", "dirigeant"}):
        raise bad_request("export_direct_orpailleur_interdit")


def _assert_can_move_to_step(db: Session, dossier: ExportDossier, target_step: str) -> None:
    if target_step not in CANONICAL_EXPORT_STEPS:
        return
    current_step = dossier.status
    if current_step not in CANONICAL_EXPORT_STEPS:
        if target_step != CANONICAL_EXPORT_STEPS[0]:
            raise bad_request("transition_export_invalide", {"from": current_step, "to": target_step})
        return
    current_index = CANONICAL_EXPORT_STEPS.index(current_step)
    target_index = CANONICAL_EXPORT_STEPS.index(target_step)
    if target_index != current_index + 1:
        raise bad_request("transition_export_invalide", {"from": current_step, "to": target_step})


def _assert_export_prerequisites(db: Session, dossier: ExportDossier, target_step: str) -> None:
    lot_ids = [row[0] for row in db.query(ExportLot.lot_id).filter(ExportLot.export_dossier_id == dossier.id).all()]
    if target_step in {"tested_certified", "export_consolidated", "dtspm_paid", "com_validated", "customs_controlled", "exported", "forex_repatriated", "closed"}:
        if not lot_ids:
            raise bad_request("lots_export_obligatoires")

    if target_step in {"tested_certified", "export_consolidated", "dtspm_paid", "com_validated", "customs_controlled", "exported", "forex_repatriated", "closed"}:
        tested_count = (
            db.query(LotTestCertificate.id)
            .filter(LotTestCertificate.lot_id.in_(lot_ids), LotTestCertificate.status == "validated")
            .count()
        ) if lot_ids else 0
        if tested_count < len(lot_ids):
            raise bad_request("lot_non_teste")

    if target_step in {"dtspm_paid", "com_validated", "customs_controlled", "exported", "forex_repatriated", "closed"}:
        due_taxes = (
            db.query(TaxRecord.id)
            .filter(TaxRecord.export_id == dossier.id, TaxRecord.status == "DUE")
            .first()
        )
        if due_taxes:
            raise bad_request("dtspm_non_acquitte")

    creator = db.query(Actor).filter(Actor.id == dossier.created_by_actor_id).first()
    if target_step in {"com_validated", "customs_controlled", "exported", "forex_repatriated", "closed"} and creator:
        if creator.agrement_status != "active":
            raise bad_request("agrement_invalide")
        if creator.sig_oc_access_status != "active":
            raise bad_request("sig_oc_suspendu")

    if target_step in {"customs_controlled", "exported", "forex_repatriated", "closed"}:
        com_ok = (
            db.query(ExportValidation.id)
            .filter(ExportValidation.export_id == dossier.id, ExportValidation.validator_role == "com", ExportValidation.decision == "approved")
            .first()
        )
        if not com_ok:
            raise bad_request("validation_com_obligatoire")

    if target_step in {"exported", "forex_repatriated", "closed"}:
        dgd_ok = (
            db.query(ExportValidation.id)
            .filter(ExportValidation.export_id == dossier.id, ExportValidation.validator_role == "dgd", ExportValidation.decision == "approved")
            .first()
        )
        if not dgd_ok:
            raise bad_request("validation_douane_obligatoire")

    if target_step in {"closed"}:
        forex_ok = (
            db.query(ForexRepatriation.id)
            .filter(ForexRepatriation.export_id == dossier.id, ForexRepatriation.status == "validated")
            .first()
        )
        if not forex_ok:
            raise bad_request("rapatriement_devises_obligatoire")


def _seed_export_checklist(db: Session, export_id: int) -> None:
    existing_count = (
        db.query(ExportChecklistItem.id)
        .filter(ExportChecklistItem.export_id == export_id)
        .count()
    )
    if existing_count > 0:
        return
    due_at = datetime.now(timezone.utc) + timedelta(hours=48)
    for doc_type in EXPORT_REQUIRED_DOC_TYPES:
        db.add(
            ExportChecklistItem(
                export_id=export_id,
                doc_type=doc_type,
                required=1,
                status="missing",
                due_at=due_at,
            )
        )


def _assert_export_checklist_complete(db: Session, dossier: ExportDossier, target_step: str) -> None:
    guarded_statuses = {
        "ready_for_control",
        "controlled",
        "sealed",
        "exported",
        "com_validated",
        "customs_controlled",
        "forex_repatriated",
        "closed",
    }
    if target_step not in guarded_statuses and target_step not in CANONICAL_EXPORT_STEPS:
        return

    _seed_export_checklist(db, dossier.id)
    now = datetime.now(timezone.utc)
    items = (
        db.query(ExportChecklistItem)
        .filter(ExportChecklistItem.export_id == dossier.id, ExportChecklistItem.required == 1)
        .all()
    )
    missing = [item.doc_type for item in items if item.status != "verified"]
    if not missing:
        return
    overdue = []
    for item in items:
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if item.status != "verified" and now > due_at:
            overdue.append(item.doc_type)
    if overdue:
        raise bad_request("dossier_incomplet_sla_depasse_48h", {"missing": missing, "overdue": overdue})
    raise bad_request("dossier_incomplet_piece_manquante", {"missing": missing})


@router.post("", response_model=ExportOut, status_code=201)
def create_export(
    payload: ExportCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    _assert_creator_allowed_for_export(db, current_actor.id)
    destination_label = payload.destination
    if payload.destination_commune_id is not None:
        destination_commune = _get_active_commune_by_id(db, payload.destination_commune_id)
        if not destination_commune:
            raise bad_request("territoire_invalide")
        destination_label = destination_commune.code
    if payload.transport_mode == "road" and payload.destination_commune_id is None:
        raise bad_request("destination_commune_obligatoire")
    sequence = db.query(ExportDossier).count() + 1
    dossier = ExportDossier(
        destination=destination_label,
        destination_commune_id=payload.destination_commune_id,
        destination_country=payload.destination_country,
        transport_mode=payload.transport_mode,
        total_weight=payload.total_weight,
        declared_value=payload.declared_value,
        status="draft",
        dossier_number=f"EXP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sequence:06d}",
        created_by_actor_id=current_actor.id,
    )
    db.add(dossier)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="export_created",
        entity_type="export",
        entity_id=str(dossier.id),
    )
    db.commit()
    db.refresh(dossier)
    return ExportOut.model_validate(dossier)


@router.get("", response_model=list[ExportOut])
def list_exports(
    status: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    created_by_actor_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    query = db.query(ExportDossier)

    is_admin = _is_admin(db, current_actor.id)
    is_dirigeant = _is_dirigeant(db, current_actor.id)
    is_commune_agent = _is_commune_agent(db, current_actor.id)

    is_export_authority = _has_any_role(db, current_actor.id, {"com", "gue", "analyse_certification"})

    if not (is_admin or is_dirigeant or is_export_authority):
        if is_commune_agent:
            creator_ids = select(Actor.id).where(Actor.commune_id == current_actor.commune_id)
            query = query.filter(ExportDossier.created_by_actor_id.in_(creator_ids))
        else:
            query = query.filter(ExportDossier.created_by_actor_id == current_actor.id)

    if status:
        query = query.filter(ExportDossier.status == status)
    if date_from:
        query = query.filter(ExportDossier.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(ExportDossier.created_at <= datetime.combine(date_to, datetime.max.time()))
    if created_by_actor_id:
        if not (is_admin or is_dirigeant or is_export_authority):
            if created_by_actor_id != current_actor.id:
                raise bad_request("acces_refuse")
        query = query.filter(ExportDossier.created_by_actor_id == created_by_actor_id)

    dossiers = query.order_by(ExportDossier.created_at.desc()).all()
    return [ExportOut.model_validate(d) for d in dossiers]


@router.get("/{export_id}", response_model=ExportOut)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")
    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")
    return ExportOut.model_validate(dossier)


@router.patch("/{export_id}/status", response_model=ExportOut)
def update_export_status(
    export_id: int,
    payload: ExportStatusUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")

    valid_statuses = {"draft", "submitted", "ready_for_control", "controlled", "sealed", "exported", "approved", "rejected", *CANONICAL_EXPORT_STEPS}
    if payload.status not in valid_statuses:
        raise bad_request("statut_invalide", {"valid_statuses": list(valid_statuses)})

    is_admin = _is_admin(db, current_actor.id)
    is_dirigeant = _is_dirigeant(db, current_actor.id)

    if payload.status in {"approved", "rejected"}:
        active_roles = _active_roles(db, current_actor.id)
        if not active_roles.intersection(EXPORT_APPROVERS):
            raise bad_request("role_insuffisant", {"required": sorted(EXPORT_APPROVERS)})

    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")

    if payload.status == "submitted":
        _seed_export_checklist(db, dossier.id)
    _assert_export_checklist_complete(db, dossier, payload.status)
    _assert_can_move_to_step(db, dossier, payload.status)
    _assert_export_prerequisites(db, dossier, payload.status)

    old_status = dossier.status
    dossier.status = payload.status
    if payload.status == "sealed":
        dossier.sealed_qr = build_qr_value("export", dossier.dossier_number or str(dossier.id))
    dossier.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dossier)

    write_audit(
        db,
        actor_id=current_actor.id,
        action="export_status_changed",
        entity_type="export",
        entity_id=str(dossier.id),
        meta={"old_status": old_status, "new_status": payload.status},
    )

    return ExportOut.model_validate(dossier)


@router.post("/{export_id}/lots", response_model=ExportOut)
def link_lots_to_export(
    export_id: int,
    payload: list[ExportLotLink],
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")

    if dossier.status != "draft":
        raise bad_request("export_non_modifiable", {"current_status": dossier.status})

    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")

    for link in payload:
        lot = db.query(Lot).filter_by(id=link.lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable", {"lot_id": link.lot_id})
        if lot.current_owner_actor_id != current_actor.id:
            raise bad_request("lot_non_proprietaire", {"lot_id": link.lot_id})
        if lot.filiere == "PIERRE":
            _ensure_active_authorization(db, current_actor.id, "PIERRE")
        if lot.filiere == "BOIS":
            _ensure_active_authorization(db, current_actor.id, "BOIS")
            essence = None
            if lot.wood_essence_id:
                essence = db.query(EssenceCatalog).filter_by(id=lot.wood_essence_id).first()
            if essence and essence.categorie == "A_protegee" and not bool(essence.export_autorise):
                approved = (
                    db.query(WorkflowApproval.id)
                    .filter(
                        WorkflowApproval.filiere == "BOIS",
                        WorkflowApproval.workflow_type == "export_exception",
                        WorkflowApproval.entity_type == "lot_export_exception",
                        WorkflowApproval.entity_id == lot.id,
                        WorkflowApproval.status == "approved",
                    )
                    .first()
                )
                if not approved:
                    raise bad_request("export_bois_bloque_essence_a")

        existing = (
            db.query(ExportLot)
            .filter(
                ExportLot.export_dossier_id == export_id,
                ExportLot.lot_id == link.lot_id,
            )
            .first()
        )
        if existing:
            existing.quantity_in_export = link.quantity_in_export
        else:
            export_lot = ExportLot(
                export_dossier_id=export_id,
                lot_id=link.lot_id,
                quantity_in_export=link.quantity_in_export,
            )
            db.add(export_lot)

    db.commit()
    db.refresh(dossier)

    write_audit(
        db,
        actor_id=current_actor.id,
        action="export_lots_linked",
        entity_type="export",
        entity_id=str(dossier.id),
        meta={"lots_count": len(payload)},
    )

    return ExportOut.model_validate(dossier)


def _get_active_commune_by_id(db: Session, commune_id: int) -> Commune | None:
    active = db.query(TerritoryVersion).filter_by(status="active").first()
    if not active:
        return None
    return (
        db.query(Commune)
        .filter(Commune.id == commune_id, Commune.version_id == active.id)
        .first()
    )


@router.post("/{export_id}/submit", response_model=ExportOut)
def submit_export_dossier(
    export_id: int,
    payload: ExportSubmitIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")
    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")
    if dossier.status not in {"draft", "submitted"}:
        raise bad_request("transition_export_invalide")
    _seed_export_checklist(db, dossier.id)
    dossier.status = "submitted"
    dossier.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dossier)
    return ExportOut.model_validate(dossier)


@router.post("/{export_id}/validate", response_model=ExportOut)
def validate_export_step(
    export_id: int,
    payload: ExportValidateIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles(EXPORT_ROLES)),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")
    step_code = (payload.step_code or "").strip().lower()
    decision = (payload.decision or "").strip().lower()
    if step_code not in {"mines", "douanes"}:
        raise bad_request("step_invalide")
    if decision not in {"approved", "rejected"}:
        raise bad_request("decision_invalide")
    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")

    db.add(
        ExportValidationStep(
            export_dossier_id=dossier.id,
            step_code=step_code,
            validator_actor_id=current_actor.id,
            decision=decision,
            notes=payload.notes,
        )
    )
    if step_code == "douanes" and decision == "approved":
        if not payload.seal_number:
            raise bad_request("seal_number_obligatoire")
        if db.query(ExportSeal).filter(ExportSeal.seal_number == payload.seal_number).first():
            raise bad_request("seal_deja_utilise")
        db.add(
            ExportSeal(
                export_dossier_id=dossier.id,
                seal_number=payload.seal_number.strip(),
                pv_document_id=payload.pv_document_id,
                sealed_by_actor_id=current_actor.id,
                status="active",
            )
        )
        links = db.query(ExportLot).filter(ExportLot.export_dossier_id == dossier.id).all()
        for lnk in links:
            lot = db.query(Lot).filter_by(id=lnk.lot_id).first()
            if lot:
                lot.status = "exported"
        dossier.status = "exported"
    elif step_code == "mines" and decision == "approved":
        dossier.status = "com_validated"
    elif decision == "rejected":
        dossier.status = "rejected"
    dossier.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dossier)
    return ExportOut.model_validate(dossier)

