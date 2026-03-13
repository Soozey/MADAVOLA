from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.bois import WorkflowApproval


class ApprovalCreateIn(BaseModel):
    filiere: str
    workflow_type: str
    entity_type: str
    entity_id: int
    reference_texte: str | None = None
    legal_todo: str | None = "TODO LEGAL"


class ApprovalDecisionIn(BaseModel):
    decision: str  # approved|rejected
    decision_notes: str | None = None
    reference_texte: str | None = None


router = APIRouter(prefix=f"{settings.api_prefix}/approvals", tags=["approvals"])


@router.post("", status_code=201)
def create_approval(
    payload: ApprovalCreateIn,
    db: Session = Depends(get_db),
    actor=Depends(get_current_actor),
):
    row = WorkflowApproval(
        filiere=payload.filiere.strip().upper(),
        workflow_type=payload.workflow_type,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        status="pending",
        reference_texte=payload.reference_texte,
        legal_todo=payload.legal_todo,
        requested_by_actor_id=actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status}


@router.post("/{approval_id}/decide")
def decide_approval(
    approval_id: int,
    payload: ApprovalDecisionIn,
    db: Session = Depends(get_db),
    actor=Depends(require_roles({"admin", "dirigeant", "forets", "bois_admin_central", "bois_douanes"})),
):
    row = db.query(WorkflowApproval).filter_by(id=approval_id).first()
    if not row:
        raise bad_request("approval_introuvable")
    decision = (payload.decision or "").strip().lower()
    if decision not in {"approved", "rejected"}:
        raise bad_request("decision_invalide")
    row.status = decision
    row.decision_notes = payload.decision_notes
    if payload.reference_texte:
        row.reference_texte = payload.reference_texte
    row.decided_by_actor_id = actor.id
    row.decided_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("", status_code=200)
def list_approvals(
    filiere: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(WorkflowApproval)
    if filiere:
        query = query.filter(WorkflowApproval.filiere == filiere.strip().upper())
    if status:
        query = query.filter(WorkflowApproval.status == status)
    rows = query.order_by(WorkflowApproval.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "filiere": r.filiere,
            "workflow_type": r.workflow_type,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "status": r.status,
            "reference_texte": r.reference_texte,
            "requested_by_actor_id": r.requested_by_actor_id,
            "decided_by_actor_id": r.decided_by_actor_id,
            "created_at": r.created_at,
            "decided_at": r.decided_at,
        }
        for r in rows
    ]
