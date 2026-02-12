from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.exports.schemas import ExportCreate, ExportOut, ExportStatusUpdate, ExportLotLink
from app.models.export import ExportDossier, ExportLot
from app.models.actor import Actor, ActorRole
from app.models.lot import Lot

router = APIRouter(prefix=f"{settings.api_prefix}/exports", tags=["exports"])


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


def _can_access_export(db: Session, current_actor: Actor, export: ExportDossier) -> bool:
    if _is_admin(db, current_actor.id) or _is_dirigeant(db, current_actor.id):
        return True
    if _is_commune_agent(db, current_actor.id):
        creator = db.query(Actor).filter_by(id=export.created_by_actor_id).first()
        if creator and creator.commune_id == current_actor.commune_id:
            return True
    if export.created_by_actor_id == current_actor.id:
        return True
    return False


@router.post("", response_model=ExportOut, status_code=201)
def create_export(
    payload: ExportCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent", "acteur"})),
):
    dossier = ExportDossier(
        destination=payload.destination,
        total_weight=payload.total_weight,
        status="draft",
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
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent", "acteur"})),
):
    query = db.query(ExportDossier)

    is_admin = _is_admin(db, current_actor.id)
    is_dirigeant = _is_dirigeant(db, current_actor.id)
    is_commune_agent = _is_commune_agent(db, current_actor.id)

    if not (is_admin or is_dirigeant):
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
        if not (is_admin or is_dirigeant):
            if created_by_actor_id != current_actor.id:
                raise bad_request("acces_refuse")
        query = query.filter(ExportDossier.created_by_actor_id == created_by_actor_id)

    dossiers = query.order_by(ExportDossier.created_at.desc()).all()
    return [ExportOut.model_validate(d) for d in dossiers]


@router.get("/{export_id}", response_model=ExportOut)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent", "acteur"})),
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
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent", "acteur"})),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")

    valid_statuses = {"draft", "submitted", "approved", "rejected"}
    if payload.status not in valid_statuses:
        raise bad_request("statut_invalide", {"valid_statuses": list(valid_statuses)})

    is_admin = _is_admin(db, current_actor.id)
    is_dirigeant = _is_dirigeant(db, current_actor.id)

    if payload.status in {"approved", "rejected"}:
        if not (is_admin or is_dirigeant):
            raise bad_request("role_insuffisant", {"required": ["admin", "dirigeant"]})

    if not _can_access_export(db, current_actor, dossier):
        raise bad_request("acces_refuse")

    old_status = dossier.status
    dossier.status = payload.status
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
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent", "acteur"})),
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

