from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.exports.schemas import ExportCreate, ExportOut
from app.models.export import ExportDossier

router = APIRouter(prefix=f"{settings.api_prefix}/exports", tags=["exports"])


@router.post("", response_model=ExportOut, status_code=201)
def create_export(
    payload: ExportCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
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
    return ExportOut(
        id=dossier.id,
        status=dossier.status,
        destination=dossier.destination,
        total_weight=float(dossier.total_weight) if dossier.total_weight is not None else None,
        created_by_actor_id=dossier.created_by_actor_id,
    )


@router.get("", response_model=list[ExportOut])
def list_exports(
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    dossiers = (
        db.query(ExportDossier)
        .filter(ExportDossier.created_by_actor_id == current_actor.id)
        .order_by(ExportDossier.created_at.desc())
        .all()
    )
    return [
        ExportOut(
            id=d.id,
            status=d.status,
            destination=d.destination,
            total_weight=float(d.total_weight) if d.total_weight is not None else None,
            created_by_actor_id=d.created_by_actor_id,
        )
        for d in dossiers
    ]


@router.get("/{export_id}", response_model=ExportOut)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    dossier = db.query(ExportDossier).filter_by(id=export_id).first()
    if not dossier:
        raise bad_request("export_introuvable")
    if dossier.created_by_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    return ExportOut(
        id=dossier.id,
        status=dossier.status,
        destination=dossier.destination,
        total_weight=float(dossier.total_weight) if dossier.total_weight is not None else None,
        created_by_actor_id=dossier.created_by_actor_id,
    )
