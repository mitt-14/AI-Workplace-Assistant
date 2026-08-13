from typing import Any

from app.services.document_analyzer import analyze_document


async def analyze_uploaded_document(
    *,
    document_id: str,
    provider: str | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    if not document_id.strip():
        raise ValueError(
            "document_id is required."
        )

    result = await analyze_document(
        document_id=document_id,
        provider=provider,
        refresh=refresh,
    )

    return result.model_dump(
        mode="json"
    )
