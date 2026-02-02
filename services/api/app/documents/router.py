import hashlib
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.documents.schemas import DocumentOut
from app.models.actor import Actor, ActorRole
from app.models.document import Document

router = APIRouter(prefix=f"{settings.api_prefix}/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=201)
def upload_document(
    doc_type: str = Form(...),
    owner_actor_id: int = Form(...),
    related_entity_type: str | None = Form(None),
    related_entity_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    actor = db.query(Actor).filter_by(id=owner_actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")
    if not _is_admin(db, current_actor.id) and owner_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    if not file.filename:
        raise bad_request("fichier_obligatoire")

    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid4().hex}{ext}"
    storage_path = storage_dir / filename

    content = file.file.read()
    if not content:
        raise bad_request("fichier_vide")

    sha256 = hashlib.sha256(content).hexdigest()
    storage_path.write_bytes(content)

    document = Document(
        doc_type=doc_type,
        owner_actor_id=owner_actor_id,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        storage_path=str(storage_path),
        original_filename=file.filename,
        sha256=sha256,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return DocumentOut(
        id=document.id,
        doc_type=document.doc_type,
        owner_actor_id=document.owner_actor_id,
        related_entity_type=document.related_entity_type,
        related_entity_id=document.related_entity_id,
        storage_path=document.storage_path,
        original_filename=document.original_filename,
        sha256=document.sha256,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(
    owner_actor_id: int | None = None,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    doc_type: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Document)
    if not _is_admin(db, current_actor.id):
        query = query.filter(Document.owner_actor_id == current_actor.id)
        if owner_actor_id and owner_actor_id != current_actor.id:
            return []
    if owner_actor_id:
        query = query.filter(Document.owner_actor_id == owner_actor_id)
    if related_entity_type:
        query = query.filter(Document.related_entity_type == related_entity_type)
    if related_entity_id:
        query = query.filter(Document.related_entity_id == related_entity_id)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    documents = query.order_by(Document.created_at.desc()).all()
    return [
        DocumentOut(
            id=doc.id,
            doc_type=doc.doc_type,
            owner_actor_id=doc.owner_actor_id,
            related_entity_type=doc.related_entity_type,
            related_entity_id=doc.related_entity_id,
            storage_path=doc.storage_path,
            original_filename=doc.original_filename,
            sha256=doc.sha256,
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    document = db.query(Document).filter_by(id=document_id).first()
    if not document:
        raise bad_request("document_introuvable")
    if not _is_admin(db, current_actor.id) and document.owner_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    return DocumentOut(
        id=document.id,
        doc_type=document.doc_type,
        owner_actor_id=document.owner_actor_id,
        related_entity_type=document.related_entity_type,
        related_entity_id=document.related_entity_id,
        storage_path=document.storage_path,
        original_filename=document.original_filename,
        sha256=document.sha256,
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
