import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_org
from ai_email_ops.app.knowledge import delete_document_chunks, ingest_text
from ai_email_ops.app.models import KnowledgeDocument, Organization
from ai_email_ops.app.text_extract import ALLOWED_EXTENSIONS, ExtractionError, extract_text

router = APIRouter(prefix="/orgs/me/knowledge", tags=["knowledge"])
logger = logging.getLogger("uvicorn.error")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_TEXT_CHARS = 300_000


class KnowledgeDocOut(BaseModel):
    id: int
    filename: str
    size_bytes: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


def clean_filename(raw: str | None) -> str:
    """Keep only the last part of the path and only printable characters."""
    name = os.path.basename((raw or "").replace("\\", "/")).strip()
    name = "".join(ch for ch in name if ch.isprintable())
    return name[:255]


@router.post("", response_model=KnowledgeDocOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    filename = clean_filename(file.filename)
    extension = os.path.splitext(filename.lower())[1]
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only .txt, .pdf and .docx files are supported")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)  # read one byte extra to detect "too big"
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (maximum 5 MB)")

    try:
        content = extract_text(filename, data)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if len(content) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail="The document contains too much text")

    document = KnowledgeDocument(organization_id=org.id, filename=filename, size_bytes=len(data))
    db.add(document)
    try:
        db.flush()  # catches a duplicate name now, before the slow embedding work
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A document with this name already exists. Delete it first to upload a new version.",
        )

    document_id = document.id
    try:
        document.chunk_count = ingest_text(org.id, document_id, filename, content)
        db.commit()
    except Exception:
        logger.exception("Knowledge ingestion failed")
        db.rollback()  # the row was never committed, so it simply disappears
        delete_document_chunks(document_id, org.id)  # remove any chunks stored before the failure
        raise HTTPException(
            status_code=503,
            detail="Could not process the document (is Ollama running?). Nothing was saved.",
        )
    db.refresh(document)
    return document


@router.get("", response_model=list[KnowledgeDocOut])
def list_documents(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    stmt = (
        select(KnowledgeDocument)
        .where(KnowledgeDocument.organization_id == org.id)
        .order_by(KnowledgeDocument.id)
    )
    return db.scalars(stmt).all()


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    document = db.get(KnowledgeDocument, document_id)
    if document is None or document.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Chunks first. If the row were deleted first and the chunk delete then failed,
    # the AI could still quote a document the CEO believes is gone.
    delete_document_chunks(document.id, org.id)
    db.delete(document)
    db.commit()