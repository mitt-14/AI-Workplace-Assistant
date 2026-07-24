import logging
import re
from pathlib import Path
from uuid import uuid4
from typing import Any
import json
from datetime import datetime, timezone

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
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentUploadResponse,
    DocumentChunkingResponse,
    DocumentIndexingResponse,
    DocumentListItem,
    DocumentListResponse,
)

from app.rag.vector_store import delete_document_chunks

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

def get_safe_stored_file_path(
    stored_filename: str,
) -> Path:
    """
    Build a safe path inside the configured upload directory.

    Path.name prevents stored metadata from using directory traversal
    values such as ../../some-file.
    """

    upload_directory = Path(
        settings.upload_directory
    )

    safe_stored_filename = Path(
        stored_filename
    ).name

    return upload_directory / safe_stored_filename

def parse_metadata_datetime(
    value: Any,
) -> datetime | None:
    """
    Parse an ISO-formatted datetime stored in document metadata.
    """

    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed_value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    except ValueError:
        return None

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(
            tzinfo=timezone.utc
        )

    return parsed_value


def get_file_modified_datetime(
    file_path: Path,
) -> datetime:
    """
    Return a file modification timestamp in UTC.
    """

    return datetime.fromtimestamp(
        file_path.stat().st_mtime,
        tz=timezone.utc,
    )

def list_document_metadata() -> list[DocumentListItem]:
    """
    Read all valid document metadata files.

    Invalid or incomplete metadata files are skipped so one corrupted
    file does not break the complete document listing.
    """

    upload_directory = Path(
        settings.upload_directory
    )

    if not upload_directory.exists():
        return []

    documents: list[DocumentListItem] = []

    for metadata_path in upload_directory.glob("*.json"):
        try:
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

        except (OSError, json.JSONDecodeError):
            logger.exception(
                "Skipping unreadable metadata file: path=%s",
                metadata_path,
            )
            continue

        required_fields = {
            "document_id",
            "original_filename",
            "stored_filename",
            "content_type",
            "size_bytes",
        }

        if not required_fields.issubset(metadata):
            logger.warning(
                "Skipping incomplete metadata file: path=%s",
                metadata_path,
            )
            continue

        indexing = metadata.get("indexing")

        if not isinstance(indexing, dict):
            indexing = {}

        uploaded_at = parse_metadata_datetime(
            metadata.get("uploaded_at")
        )

        if uploaded_at is None:
            try:
                uploaded_at = (
                    get_file_modified_datetime(
                        metadata_path
                    )
                )

            except OSError:
                logger.exception(
                    "Could not determine upload time: path=%s",
                    metadata_path,
                )
                continue

        indexed_at = parse_metadata_datetime(
            indexing.get("indexed_at")
        )

        status = indexing.get(
            "status",
            "uploaded",
        )

        documents.append(
            DocumentListItem(
                document_id=metadata["document_id"],
                original_filename=metadata[
                    "original_filename"
                ],
                stored_filename=metadata[
                    "stored_filename"
                ],
                content_type=metadata[
                    "content_type"
                ],
                size_bytes=metadata["size_bytes"],
                page_count=indexing.get(
                    "page_count"
                ),
                chunk_count=indexing.get(
                    "chunk_count"
                ),
                stored_chunk_count=indexing.get(
                    "stored_chunk_count"
                ),
                embedding_model=indexing.get(
                    "embedding_model"
                ),
                collection_name=indexing.get(
                    "collection_name"
                ),
                uploaded_at=uploaded_at,
                indexed_at=indexed_at,
                status=status,
            )
        )

    documents.sort(
        key=lambda document: document.uploaded_at,
        reverse=True,
    )

    return documents

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
    "content_type": (
        file.content_type
        or "application/octet-stream"
    ),
    "size_bytes": len(file_content),
    "uploaded_at": datetime.now(
        timezone.utc
    ).isoformat(),
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
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
)
async def list_documents() -> DocumentListResponse:
    """
    Return all uploaded documents and their indexing status.
    """

    documents = list_document_metadata()

    logger.info(
        "Document listing completed: total=%s",
        len(documents),
    )

    return DocumentListResponse(
        total=len(documents),
        documents=documents,
    )

@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
)
async def get_document_details(
    document_id: str,
) -> DocumentDetailResponse:
    """
    Return upload metadata and indexing statistics for one document.
    """

    metadata = load_document_metadata(
        document_id
    )

    upload_directory = Path(
        settings.upload_directory
    )

    metadata_path = (
        upload_directory
        / f"{document_id}.json"
    )

    file_path = (
        upload_directory
        / metadata["stored_filename"]
    )

    indexing = metadata.get("indexing")

    if not isinstance(indexing, dict):
        indexing = {}

    uploaded_at = parse_metadata_datetime(
        metadata.get("uploaded_at")
    )

    if uploaded_at is None:
        uploaded_at = get_file_modified_datetime(
            metadata_path
        )

    indexed_at = parse_metadata_datetime(
        indexing.get("indexed_at")
    )

    status = indexing.get(
        "status",
        "uploaded",
    )

    logger.info(
        "Document details retrieved: "
        "document_id=%s status=%s",
        document_id,
        status,
    )

    return DocumentDetailResponse(
        document_id=metadata["document_id"],
        original_filename=metadata[
            "original_filename"
        ],
        stored_filename=metadata[
            "stored_filename"
        ],
        content_type=metadata["content_type"],
        size_bytes=metadata.get(
            "size_bytes",
            0,
        ),
        file_exists=(
            file_path.exists()
            and file_path.is_file()
        ),
        page_count=indexing.get(
            "page_count"
        ),
        chunk_count=indexing.get(
            "chunk_count"
        ),
        stored_chunk_count=indexing.get(
            "stored_chunk_count"
        ),
        embedding_model=indexing.get(
            "embedding_model"
        ),
        embedding_dimensions=indexing.get(
            "embedding_dimensions"
        ),
        collection_name=indexing.get(
            "collection_name"
        ),
        uploaded_at=uploaded_at,
        indexed_at=indexed_at,
        status=status,
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
        "page_count": result["page_count"],
        "chunk_count": result["chunk_count"],
        "stored_chunk_count": result[
            "stored_chunk_count"
        ],
        "embedding_model": result["embedding_model"],
        "embedding_dimensions": result[
            "embedding_dimensions"
        ],
        "collection_name": (
            settings.chroma_collection_name
        ),
        "indexed_at": datetime.now(
            timezone.utc
        ).isoformat(),
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

@router.post(
    "/{document_id}/reindex",
    response_model=DocumentIndexingResponse,
    summary="Re-index an uploaded document",
)
async def reindex_uploaded_document(
    document_id: str,
) -> DocumentIndexingResponse:
    """
    Delete existing vector chunks and index the stored document again.
    """

    metadata = load_document_metadata(document_id)

    upload_directory = Path(settings.upload_directory)
    metadata_path = upload_directory / f"{document_id}.json"

    file_path = get_document_file_path(
        document_id=document_id,
        metadata=metadata,
    )

    logger.info(
    "Starting document re-indexing: document_id=%s",
    document_id,
    )
    
    try:
        delete_document_chunks(
            document_id=document_id,
        )
    
    except Exception as exc:
        logger.exception(
            "Failed to delete existing vectors: document_id=%s",
            document_id,
        )
    
        raise DocumentIndexingError(
            "Existing document vectors could not be deleted."
        ) from exc
    
    try:
        result = index_document(
            document_id=document_id,
            file_path=file_path,
            original_filename=metadata["original_filename"],
            content_type=metadata["content_type"],
        )
    
    except Exception:
        logger.exception(
            "Document re-indexing failed: document_id=%s",
            document_id,
        )
        raise

    except Exception:
        logger.exception(
            "Document re-indexing failed after old vectors "
            "were removed: document_id=%s",
            document_id,
        )
        raise

    reindexed_at = datetime.now(
        timezone.utc
    ).isoformat()

    metadata["indexing"] = {
        "status": "indexed",
        "page_count": result["page_count"],
        "chunk_count": result["chunk_count"],
        "stored_chunk_count": result[
            "stored_chunk_count"
        ],
        "embedding_model": result[
            "embedding_model"
        ],
        "embedding_dimensions": result[
            "embedding_dimensions"
        ],
        "collection_name": (
            settings.chroma_collection_name
        ),
        "indexed_at": reindexed_at,
        "reindexed_at": reindexed_at,
    }

    try:
        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

    except OSError as exc:
        logger.exception(
            "Document was re-indexed but metadata update failed: "
            "document_id=%s",
            document_id,
        )

        raise DocumentIndexingError(
            "The document was re-indexed, but its metadata "
            "could not be updated."
        ) from exc

    logger.info(
        "Document re-indexed successfully: "
        "document_id=%s chunks=%s",
        document_id,
        result["stored_chunk_count"],
    )

    return DocumentIndexingResponse(
        document_id=document_id,
        filename=metadata[
            "original_filename"
        ],
        page_count=result[
            "page_count"
        ],
        extracted_character_count=result[
            "extracted_character_count"
        ],
        chunk_count=result[
            "chunk_count"
        ],
        stored_chunk_count=result[
            "stored_chunk_count"
        ],
        embedding_model=result[
            "embedding_model"
        ],
        embedding_dimensions=result[
            "embedding_dimensions"
        ],
        collection_name=(
            settings.chroma_collection_name
        ),
        status="reindexed",
    )

@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
)
async def delete_document(
    document_id: str,
) -> DocumentDeleteResponse:
    """
    Delete a document's vector chunks, uploaded file and metadata.
    """

    metadata = load_document_metadata(
        document_id
    )

    upload_directory = Path(
        settings.upload_directory
    )

    metadata_path = (
        upload_directory
        / f"{document_id}.json"
    )

    file_path = get_safe_stored_file_path(
        metadata["stored_filename"]
    )

    filename = metadata["original_filename"]

    deleted_chunks = False
    deleted_file = False
    deleted_metadata = False

    # Delete vectors before removing metadata so the operation can
    # still be retried if ChromaDB deletion fails.
    delete_document_chunks(
        document_id=document_id
    )
    deleted_chunks = True

    try:
        if file_path.exists():
            file_path.unlink()
            deleted_file = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted_metadata = True

    except OSError as exc:
        logger.exception(
            "Failed to delete document files: "
            "document_id=%s file=%s",
            document_id,
            file_path,
        )

        raise DocumentIndexingError(
            "The document vectors were removed, but its stored "
            "files could not be completely deleted."
        ) from exc

    logger.info(
        "Document deleted successfully: "
        "document_id=%s file_deleted=%s "
        "metadata_deleted=%s chunks_deleted=%s",
        document_id,
        deleted_file,
        deleted_metadata,
        deleted_chunks,
    )

    return DocumentDeleteResponse(
        document_id=document_id,
        filename=filename,
        deleted_file=deleted_file,
        deleted_metadata=deleted_metadata,
        deleted_chunks=deleted_chunks,
        status="deleted",
    )