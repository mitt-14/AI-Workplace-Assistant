import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.rag.document_loader import extract_document_pages
from app.rag.embedding_service import embed_documents
from app.rag.text_splitter import split_document_text
from app.rag.vector_store import (
    delete_document_chunks,
    store_document_chunks,
)

logger = logging.getLogger(__name__)


def index_document(
    *,
    document_id: str,
    file_path: Path,
    original_filename: str,
    content_type: str,
) -> dict[str, Any]:
    """
    Run the complete page-aware document-indexing pipeline.

    Steps:
    1. Extract document text page by page.
    2. Split each page into overlapping chunks.
    3. Assign globally unique chunk IDs and indexes.
    4. Generate embeddings.
    5. Store chunks with page metadata in ChromaDB.
    """

    try:
        extracted_document = extract_document_pages(
            file_path=file_path,
            content_type=content_type,
        )

        chunk_ids: list[str] = []
        chunk_texts: list[str] = []
        chunk_metadata: list[dict[str, Any]] = []

        global_chunk_index = 0
        extracted_character_count = 0

        for page in extracted_document.pages:
            page_text = page.text or ""
            extracted_character_count += len(page_text)

            # PDF pages can occasionally contain no extractable text.
            if not page_text.strip():
                logger.debug(
                    "Skipping empty document page: "
                    "document_id=%s page_number=%s",
                    document_id,
                    page.page_number,
                )
                continue

            # A page-specific temporary ID prevents duplicate IDs while
            # split_document_text starts its local index from zero.
            temporary_document_id = (
                f"{document_id}_page_{page.page_number}"
            )

            page_chunks = split_document_text(
                text=page_text,
                document_id=temporary_document_id,
            )

            for page_chunk in page_chunks:
                chunk_id = (
                    f"{document_id}_chunk_{global_chunk_index}"
                )

                chunk_ids.append(chunk_id)
                chunk_texts.append(page_chunk.text)

                chunk_metadata.append(
                    {
                        "document_id": document_id,
                        "filename": original_filename,
                        "content_type": content_type,
                        "page_number": int(page.page_number),
                        "chunk_index": global_chunk_index,
                        "page_chunk_index": page_chunk.index,
                        "character_count": (
                            page_chunk.character_count
                        ),
                    }
                )

                global_chunk_index += 1

        if not chunk_texts:
            raise ValueError(
                "The document contains no extractable text "
                "that can be indexed."
            )

        embeddings = embed_documents(
            chunk_texts
        )

        if len(embeddings) != len(chunk_texts):
            raise ValueError(
                "Embedding count does not match document "
                "chunk count."
            )

        # Remove old chunks before storing the newly indexed version.
        # This is important when chunk size, overlap, or page extraction
        # configuration changes.
        delete_document_chunks(
            document_id
        )

        logger.warning(
            "PAGE METADATA TEST: %s",
            chunk_metadata[:5],
        )

        stored_chunk_count = store_document_chunks(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadata,
        )

    except Exception:
        logger.exception(
            "Document indexing failed: "
            "document_id=%s filename=%s",
            document_id,
            original_filename,
        )
        raise

    embedding_dimensions = (
        len(embeddings[0])
        if embeddings
        else 0
    )

    logger.info(
        "Document indexed successfully: "
        "document_id=%s pages=%s chunks=%s "
        "stored_chunks=%s dimensions=%s",
        document_id,
        extracted_document.total_pages,
        len(chunk_texts),
        stored_chunk_count,
        embedding_dimensions,
    )

    return {
        "page_count": extracted_document.total_pages,
        "extracted_character_count": (
            extracted_character_count
        ),
        "chunk_count": len(chunk_texts),
        "stored_chunk_count": stored_chunk_count,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": embedding_dimensions,
    }