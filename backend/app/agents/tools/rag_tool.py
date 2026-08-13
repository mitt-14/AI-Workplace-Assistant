import asyncio
from typing import Any

from app.core.config import settings
from app.rag.retriever import semantic_search


async def search_company_documents(
    *,
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
) -> dict[str, Any]:
    """
    Search indexed company documents without making another
    answer-generation LLM call.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError(
            "query is required for document search."
        )

    top_k = max(
        1,
        min(
            int(top_k),
            settings.maximum_search_results,
        ),
    )

    results = await asyncio.to_thread(
        semantic_search,
        query=cleaned_query,
        top_k=top_k,
        document_id=document_id,
    )

    return {
        "query": cleaned_query,
        "result_count": len(results),
        "results": results,
    }
