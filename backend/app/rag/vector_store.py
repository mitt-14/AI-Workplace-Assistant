import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Create a persistent local ChromaDB client.
    """

    database_path = Path(settings.chroma_directory)
    database_path.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(
        path=str(database_path),
    )


def get_document_collection() -> Collection:
    """
    Return the application's document collection.

    The application calculates embeddings itself through Ollama,
    so the collection receives embeddings directly.
    """

    try:
        client = get_chroma_client()

        collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={
                "description": (
                    "Chunks indexed by the AI Workplace Assistant"
                )
            },
        )

        return collection

    except Exception as exc:
        logger.exception(
            "Failed to access Chroma collection: collection=%s",
            settings.chroma_collection_name,
        )

        raise VectorStoreError(
            "Could not access the ChromaDB collection."
        ) from exc


def store_document_chunks(
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
) -> int:
    """
    Insert or update document chunks in ChromaDB.

    Upsert makes indexing repeatable:
    existing chunk IDs are updated rather than duplicated.
    """

    if not ids:
        raise VectorStoreError(
            "No chunks were supplied for vector storage."
        )

    item_count = len(ids)

    if not (
        len(documents)
        == item_count
        == len(embeddings)
        == len(metadatas)
    ):
        raise VectorStoreError(
            "IDs, documents, embeddings and metadata must have "
            "matching lengths."
        )

    try:
        collection = get_document_collection()

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    except Exception as exc:
        logger.exception(
            "Failed to store document chunks: count=%s",
            item_count,
        )

        raise VectorStoreError(
            "The document chunks could not be stored in ChromaDB."
        ) from exc

    logger.info(
        "Document chunks stored: collection=%s count=%s",
        settings.chroma_collection_name,
        item_count,
    )

    return item_count


def delete_document_chunks(document_id: str) -> None:
    """
    Delete all chunks belonging to one document.
    """

    try:
        collection = get_document_collection()

        collection.delete(
            where={"document_id": document_id},
        )

    except Exception as exc:
        logger.exception(
            "Failed to delete old chunks: document_id=%s",
            document_id,
        )

        raise VectorStoreError(
            "Existing document chunks could not be deleted."
        ) from exc