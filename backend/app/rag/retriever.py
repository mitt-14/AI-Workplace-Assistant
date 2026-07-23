import logging
from typing import Any

from app.core.config import settings
from app.core.exceptions import SemanticSearchError
from app.rag.embedding_service import embed_query
from app.rag.vector_store import search_document_chunks

logger = logging.getLogger(__name__)


def distance_to_relevance(distance: float) -> float:
    """
    Convert vector distance into a readable relevance value.

    This value is useful for display and ranking, but it should not
    be interpreted as a calibrated probability.
    """

    if distance < 0:
        distance = 0

    score = 1.0 / (1.0 + distance)

    return round(score, 4)


def semantic_search(
    *,
    query: str,
    top_k: int,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Embed a query and retrieve the closest document chunks.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise SemanticSearchError(
            "The semantic-search query cannot be empty."
        )

    try:
        query_embedding = embed_query(cleaned_query)

        raw_results = search_document_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id,
        )
    except Exception:
        logger.exception(
            "Semantic search failed: query=%s document_id=%s",
            cleaned_query,
            document_id,
        )
        raise

    ids = raw_results.get("ids") or [[]]
    documents = raw_results.get("documents") or [[]]
    metadatas = raw_results.get("metadatas") or [[]]
    distances = raw_results.get("distances") or [[]]

    result_ids = ids[0] if ids else []
    result_documents = documents[0] if documents else []
    result_metadatas = metadatas[0] if metadatas else []
    result_distances = distances[0] if distances else []

    search_results: list[dict[str, Any]] = []

    for chunk_id, text, metadata, distance in zip(
        result_ids,
        result_documents,
        result_metadatas,
        result_distances,
    ):
        metadata = metadata or {}
        numeric_distance = float(distance)

        raw_page_number = metadata.get(
            "page_number"
        )

        page_number: int | None = None

        if raw_page_number is not None:
            try:
                parsed_page_number = int(
                    raw_page_number
                )

                if parsed_page_number >= 1:
                    page_number = parsed_page_number

            except (
                TypeError,
                ValueError,
            ):
                logger.warning(
                    "Ignoring invalid page metadata: "
                    "chunk_id=%s page_number=%r",
                    chunk_id,
                    raw_page_number,
                )

        search_results.append(
            {
                "chunk_id": str(chunk_id),
                "document_id": str(
                    metadata.get(
                        "document_id",
                        "",
                    )
                ),
                "filename": str(
                    metadata.get(
                        "filename",
                        "Unknown document",
                    )
                ),
                "page_number": page_number,
                "chunk_index": int(
                    metadata.get(
                        "chunk_index",
                        0,
                    )
                ),
                "text": text or "",
                "distance": round(
                    numeric_distance,
                    6,
                ),
                "relevance_score": distance_to_relevance(
                    numeric_distance
                ),
            }
        )

    logger.info(
        "Semantic search completed: results=%s model=%s "
        "document_id=%s",
        len(search_results),
        settings.embedding_model,
        document_id,
    )

    return search_results