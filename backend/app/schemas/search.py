from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Question or text used for semantic search.",
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of matching chunks to return.",
    )

    document_id: str | None = Field(
        default=None,
        description="Optionally restrict search to one document.",
    )


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    text: str
    distance: float
    relevance_score: float


class SemanticSearchResponse(BaseModel):
    query: str
    result_count: int
    embedding_model: str
    results: list[SearchResultItem]
    status: str