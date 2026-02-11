from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin.schemas import (
    ActorRoleAssign,
    ActorRoleOut,
    ActorRoleUpdate,
    SystemConfigCreate,
    SystemConfigOut,
    SystemConfigUpdate,
)
from app.auth.dependencies import require_roles
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.admin import SystemConfig
from app.models.actor import Actor, ActorRole

router = APIRouter(prefix=f"{settings.api_prefix}/admin", tags=["admin"])


# System Config endpoints
@router.post("/config", response_model=SystemConfigOut, status_code=201)
def create_config(
    payload: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    existing = db.query(SystemConfig).filter_by(key=payload.key).first()
    if existing:
        raise bad_request("config_key_exists", {"key": payload.key})

    config = SystemConfig(
        key=payload.key,
        value=payload.value,
        description=payload.description,
        updated_by_actor_id=current_actor.id,
    )
    db.add(config)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="config_created",
        entity_type="system_config",
        entity_id=str(config.id),
        meta={"key": payload.key},
    )
    db.commit()
    db.refresh(config)
    return SystemConfigOut.model_validate(config)


@router.get("/config", response_model=list[SystemConfigOut])
def list_configs(
    key: str | None = Query(None),
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    query = db.query(SystemConfig)
    if key:
        query = query.filter(SystemConfig.key.ilike(f"%{key}%"))
    configs = query.order_by(SystemConfig.key).all()
    return [SystemConfigOut.model_validate(c) for c in configs]


@router.get("/config/{config_id}", response_model=SystemConfigOut)
def get_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    config = db.query(SystemConfig).filter_by(id=config_id).first()
    if not config:
        raise bad_request("config_introuvable")
    return SystemConfigOut.model_validate(config)


@router.patch("/config/{config_id}", response_model=SystemConfigOut)
def update_config(
    config_id: int,
    payload: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    config = db.query(SystemConfig).filter_by(id=config_id).first()
    if not config:
        raise bad_request("config_introuvable")

    old_value = config.value
    if payload.value is not None:
        config.value = payload.value
    if payload.description is not None:
        config.description = payload.description
    config.updated_by_actor_id = current_actor.id
    config.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(config)

    write_audit(
        db,
        actor_id=current_actor.id,
        action="config_updated",
        entity_type="system_config",
        entity_id=str(config.id),
        meta={"key": config.key, "old_value": old_value, "new_value": config.value},
    )

    return SystemConfigOut.model_validate(config)


@router.delete("/config/{config_id}", status_code=204)
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    config = db.query(SystemConfig).filter_by(id=config_id).first()
    if not config:
        raise bad_request("config_introuvable")

    key = config.key
    db.delete(config)
    db.commit()

    write_audit(
        db,
        actor_id=current_actor.id,
        action="config_deleted",
        entity_type="system_config",
        entity_id=str(config_id),
        meta={"key": key},
    )


# Actor Role Management endpoints
@router.post("/actors/{actor_id}/roles", response_model=ActorRoleOut, status_code=201)
def assign_role(
    actor_id: int,
    payload: ActorRoleAssign,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")

    # Check if role already exists
    existing = (
        db.query(ActorRole)
        .filter_by(actor_id=actor_id, role=payload.role)
        .filter(ActorRole.status == "active")
        .first()
    )
    if existing:
        raise bad_request("role_deja_attribue", {"role": payload.role})

    role = ActorRole(
        actor_id=actor_id,
        role=payload.role,
        status="active",
        valid_from=payload.valid_from or datetime.now(timezone.utc),
        valid_to=payload.valid_to,
    )
    db.add(role)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="role_assigned",
        entity_type="actor_role",
        entity_id=str(role.id),
        meta={"target_actor_id": actor_id, "role": payload.role},
    )
    db.commit()
    db.refresh(role)
    return ActorRoleOut.model_validate(role)


@router.get("/actors/{actor_id}/roles", response_model=list[ActorRoleOut])
def list_actor_roles(
    actor_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")

    roles = db.query(ActorRole).filter_by(actor_id=actor_id).order_by(ActorRole.role).all()
    return [ActorRoleOut.model_validate(r) for r in roles]


@router.patch("/roles/{role_id}", response_model=ActorRoleOut)
def update_role(
    role_id: int,
    payload: ActorRoleUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    role = db.query(ActorRole).filter_by(id=role_id).first()
    if not role:
        raise bad_request("role_introuvable")

    old_status = role.status
    if payload.status is not None:
        role.status = payload.status
    if payload.valid_from is not None:
        role.valid_from = payload.valid_from
    if payload.valid_to is not None:
        role.valid_to = payload.valid_to

    db.commit()
    db.refresh(role)

    write_audit(
        db,
        actor_id=current_actor.id,
        action="role_updated",
        entity_type="actor_role",
        entity_id=str(role_id),
        meta={"actor_id": role.actor_id, "role": role.role, "old_status": old_status, "new_status": role.status},
    )

    return ActorRoleOut.model_validate(role)


@router.delete("/roles/{role_id}", status_code=204)
def revoke_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin"})),
):
    role = db.query(ActorRole).filter_by(id=role_id).first()
    if not role:
        raise bad_request("role_introuvable")

    actor_id = role.actor_id
    role_name = role.role
    db.delete(role)
    db.commit()

    write_audit(
        db,
        actor_id=current_actor.id,
        action="role_revoked",
        entity_type="actor_role",
        entity_id=str(role_id),
        meta={"target_actor_id": actor_id, "role": role_name},
    )

