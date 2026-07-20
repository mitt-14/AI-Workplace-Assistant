import logging

from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.core.exceptions import EmbeddingServiceError

logger = logging.getLogger(__name__)


def get_embedding_model() -> OllamaEmbeddings:
    """
    Create an Ollama embedding client.

    The returned object can generate embeddings for:
    - document chunks;
    - user search queries.
    """

    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple document chunks.
    """

    if not texts:
        raise EmbeddingServiceError(
            "No text was provided for embedding."
        )

    try:
        embedding_model = get_embedding_model()
        embeddings = embedding_model.embed_documents(texts)
    except Exception as exc:
        logger.exception(
            "Document embedding failed: model=%s text_count=%s",
            settings.embedding_model,
            len(texts),
        )

        raise EmbeddingServiceError(
            message=(
                "Could not generate document embeddings. "
                f"Make sure Ollama is running and the "
                f"'{settings.embedding_model}' model is installed."
            )
        ) from exc

    if len(embeddings) != len(texts):
        raise EmbeddingServiceError(
            "The embedding service returned an unexpected result count."
        )

    if not embeddings or not embeddings[0]:
        raise EmbeddingServiceError(
            "The embedding service returned empty embeddings."
        )

    logger.info(
        "Document embeddings generated: model=%s text_count=%s "
        "dimensions=%s",
        settings.embedding_model,
        len(texts),
        len(embeddings[0]),
    )

    return embeddings


def embed_query(query: str) -> list[float]:
    """
    Generate one embedding for a semantic-search query.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise EmbeddingServiceError(
            "The search query cannot be empty."
        )

    try:
        embedding_model = get_embedding_model()
        embedding = embedding_model.embed_query(cleaned_query)
    except Exception as exc:
        logger.exception(
            "Query embedding failed: model=%s",
            settings.embedding_model,
        )

        raise EmbeddingServiceError(
            message=(
                "Could not generate the query embedding. "
                f"Make sure Ollama is running and the "
                f"'{settings.embedding_model}' model is installed."
            )
        ) from exc

    if not embedding:
        raise EmbeddingServiceError(
            "The embedding service returned an empty query embedding."
        )

    return embedding