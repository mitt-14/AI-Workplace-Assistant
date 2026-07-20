import logging
from pathlib import Path
from typing import Any

from app.core.exceptions import DocumentIndexingError
from app.rag.document_loader import extract_document_text
from app.rag.embedding_service import embed_documents
from app.rag.text_splitter import split_document_text
from app.rag.vector_store import (
    delete_document_chunks,
    store_document_chunks,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


def index_document(
    *,
    document_id: str,
    file_path: Path,
    original_filename: str,
    content_type: str,
) -> dict[str, Any]:
    """
    Run the complete document-indexing pipeline.

    Steps:
    1. Extract text.
    2. Clean and split it.
    3. Generate embeddings.
    4. Store chunks and metadata in ChromaDB.
    """

    try:
        extracted_text, page_count = extract_document_text(
            file_path=file_path,
            content_type=content_type,
        )

        chunks = split_document_text(
            text=extracted_text,
            document_id=document_id,
        )

        chunk_texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = embed_documents(chunk_texts)

        chunk_ids = [
            chunk.chunk_id
            for chunk in chunks
        ]

        chunk_metadata = [
            {
                "document_id": document_id,
                "filename": original_filename,
                "content_type": content_type,
                "chunk_index": chunk.index,
                "character_count": chunk.character_count,
            }
            for chunk in chunks
        ]

        # Remove old chunks in case chunking configuration changed.
        delete_document_chunks(document_id)

        stored_chunk_count = store_document_chunks(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadata,
        )

    except Exception:
        logger.exception(
            "Document indexing failed: document_id=%s",
            document_id,
        )
        raise

    embedding_dimensions = (
        len(embeddings[0])
        if embeddings
        else 0
    )

    logger.info(
        "Document indexed successfully: document_id=%s chunks=%s "
        "dimensions=%s",
        document_id,
        stored_chunk_count,
        embedding_dimensions,
    )

    return {
        "page_count": page_count,
        "extracted_character_count": len(extracted_text),
        "chunk_count": len(chunks),
        "stored_chunk_count": stored_chunk_count,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": embedding_dimensions,
    }