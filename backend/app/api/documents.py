import logging
import re
from pathlib import Path
from uuid import uuid4
from typing import Any
import json

from fastapi import APIRouter, File, UploadFile

from app.core.config import settings
from app.core.exceptions import (
    DocumentIndexingError,
    DocumentNotFoundError,
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.rag.document_loader import extract_document_text
from app.rag.indexing_service import index_document
from app.rag.text_splitter import (
    clean_document_text,
    split_document_text,
)
from app.schemas.document import (
    DocumentExtractionResponse,
    DocumentUploadResponse,
    DocumentChunkingResponse,
    DocumentIndexingResponse,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Remove unsafe characters from an uploaded filename.
    """

    safe_name = Path(filename).name
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", safe_name)

    return safe_name or "document"

def load_document_metadata(document_id: str) -> dict[str, Any]:
    """
    Read and validate metadata for an uploaded document.
    """

    upload_directory = Path(settings.upload_directory)
    metadata_path = upload_directory / f"{document_id}.json"

    if not metadata_path.exists():
        raise DocumentNotFoundError(document_id)

    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception(
            "Failed to read document metadata: document_id=%s",
            document_id,
        )
        raise DocumentNotFoundError(document_id) from exc

    required_fields = {
        "document_id",
        "original_filename",
        "stored_filename",
        "content_type",
    }

    if not required_fields.issubset(metadata):
        logger.error(
            "Document metadata is incomplete: document_id=%s",
            document_id,
        )
        raise DocumentIndexingError(
            "The stored document metadata is incomplete."
        )

    return metadata


def get_document_file_path(
    document_id: str,
    metadata: dict[str, Any],
) -> Path:
    """
    Return the stored document path and confirm that it exists.
    """

    upload_directory = Path(settings.upload_directory)
    file_path = upload_directory / metadata["stored_filename"]

    if not file_path.exists() or not file_path.is_file():
        raise DocumentNotFoundError(document_id)

    return file_path


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Upload a document",
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    allowed_types = {
        content_type.strip()
        for content_type in settings.allowed_file_types.split(",")
    }

    if file.content_type not in allowed_types:
        raise UnsupportedFileTypeError(
            file.content_type or "unknown",
        )

    file_content = await file.read()

    if not file_content:
        raise EmptyFileError()

    maximum_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    if len(file_content) > maximum_size_bytes:
        raise FileTooLargeError(settings.max_upload_size_mb)

    document_id = str(uuid4())
    original_filename = file.filename or "document"
    safe_filename = sanitize_filename(original_filename)

    stored_filename = f"{document_id}_{safe_filename}"

    upload_directory = Path(settings.upload_directory)
    upload_directory.mkdir(parents=True, exist_ok=True)

    file_path = upload_directory / stored_filename
    file_path.write_bytes(file_content)
    
    metadata = {
    "document_id": document_id,
    "original_filename": original_filename,
    "stored_filename": stored_filename,
    "content_type": file.content_type or "application/octet-stream",
    "size_bytes": len(file_content),
    }

    metadata_path = upload_directory / f"{document_id}.json"

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "Document uploaded successfully: document_id=%s filename=%s size=%s",
        document_id,
        safe_filename,
        len(file_content),
    )

    return DocumentUploadResponse(
        document_id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(file_content),
        status="uploaded",
    )

@router.get(
    "/{document_id}/text",
    response_model=DocumentExtractionResponse,
    summary="Extract text from an uploaded document",
)
async def get_document_text(
    document_id: str,
) -> DocumentExtractionResponse:
    upload_directory = Path(settings.upload_directory)
    metadata_path = upload_directory / f"{document_id}.json"

    if not metadata_path.exists():
        raise DocumentNotFoundError(document_id)

    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception(
            "Failed to read document metadata: document_id=%s",
            document_id,
        )

        raise DocumentNotFoundError(document_id) from exc

    file_path = upload_directory / metadata["stored_filename"]

    if not file_path.exists():
        raise DocumentNotFoundError(document_id)

    text, page_count = extract_document_text(
        file_path=file_path,
        content_type=metadata["content_type"],
    )

    logger.info(
        "Document extraction completed: document_id=%s characters=%s",
        document_id,
        len(text),
    )

    return DocumentExtractionResponse(
        document_id=document_id,
        filename=metadata["original_filename"],
        content_type=metadata["content_type"],
        page_count=page_count,
        character_count=len(text),
        text=text,
        status="extracted",
    )


@router.get(
    "/{document_id}/chunks",
    response_model=DocumentChunkingResponse,
    summary="Extract and split an uploaded document",
)
async def get_document_chunks(
    document_id: str,
) -> DocumentChunkingResponse:
    upload_directory = Path(settings.upload_directory)
    metadata_path = upload_directory / f"{document_id}.json"

    if not metadata_path.exists():
        raise DocumentNotFoundError(document_id)

    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception(
            "Failed to read document metadata: document_id=%s",
            document_id,
        )

        raise DocumentNotFoundError(document_id) from exc

    file_path = upload_directory / metadata["stored_filename"]

    if not file_path.exists():
        raise DocumentNotFoundError(document_id)

    extracted_text, _ = extract_document_text(
        file_path=file_path,
        content_type=metadata["content_type"],
    )

    cleaned_text = clean_document_text(extracted_text)

    chunks = split_document_text(
        text=extracted_text,
        document_id=document_id,
    )

    logger.info(
        "Document chunking completed: document_id=%s chunks=%s",
        document_id,
        len(chunks),
    )

    return DocumentChunkingResponse(
        document_id=document_id,
        filename=metadata["original_filename"],
        original_character_count=len(extracted_text),
        cleaned_character_count=len(cleaned_text),
        chunk_count=len(chunks),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        chunks=[
            {
                "chunk_id": chunk.chunk_id,
                "index": chunk.index,
                "text": chunk.text,
                "character_count": chunk.character_count,
            }
            for chunk in chunks
        ],
        status="chunked",
    )

@router.post(
    "/{document_id}/index",
    response_model=DocumentIndexingResponse,
    summary="Generate embeddings and index a document",
)
async def index_uploaded_document(
    document_id: str,
) -> DocumentIndexingResponse:
    upload_directory = Path(settings.upload_directory)
    metadata_path = upload_directory / f"{document_id}.json"

    if not metadata_path.exists():
        raise DocumentNotFoundError(document_id)

    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception(
            "Failed to read document metadata: document_id=%s",
            document_id,
        )

        raise DocumentNotFoundError(document_id) from exc

    required_fields = {
        "stored_filename",
        "original_filename",
        "content_type",
    }

    if not required_fields.issubset(metadata):
        logger.error(
            "Document metadata is incomplete: document_id=%s",
            document_id,
        )

        raise DocumentIndexingError(
            "The stored document metadata is incomplete."
        )

    file_path = (
        upload_directory
        / metadata["stored_filename"]
    )

    if not file_path.exists():
        raise DocumentNotFoundError(document_id)

    result = index_document(
        document_id=document_id,
        file_path=file_path,
        original_filename=metadata["original_filename"],
        content_type=metadata["content_type"],
    )

    metadata["indexing"] = {
        "status": "indexed",
        "chunk_count": result["chunk_count"],
        "stored_chunk_count": result["stored_chunk_count"],
        "embedding_model": result["embedding_model"],
        "embedding_dimensions": result[
            "embedding_dimensions"
        ],
        "collection_name": settings.chroma_collection_name,
    }

    try:
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.exception(
            "Failed to update indexing metadata: document_id=%s",
            document_id,
        )

        raise DocumentIndexingError(
            "The document was indexed, but its metadata "
            "could not be updated."
        ) from exc

    return DocumentIndexingResponse(
        document_id=document_id,
        filename=metadata["original_filename"],
        page_count=result["page_count"],
        extracted_character_count=result[
            "extracted_character_count"
        ],
        chunk_count=result["chunk_count"],
        stored_chunk_count=result["stored_chunk_count"],
        embedding_model=result["embedding_model"],
        embedding_dimensions=result[
            "embedding_dimensions"
        ],
        collection_name=settings.chroma_collection_name,
        status="indexed",
    )