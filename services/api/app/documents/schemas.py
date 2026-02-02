from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    doc_type: str
    owner_actor_id: int
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    storage_path: str
    original_filename: str
    sha256: str
