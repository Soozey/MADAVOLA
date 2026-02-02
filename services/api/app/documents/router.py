import hashlib
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.documents.schemas import DocumentOut
from app.models.actor import Actor
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
):
    actor = db.query(Actor).filter_by(id=owner_actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")
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
