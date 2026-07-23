from typing import Literal

from pydantic import BaseModel, Field


class RagChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Question to answer using indexed documents.",
    )

    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID for persistent memory.",
    )

    provider: Literal["ollama", "gemini"] = Field(
        default="ollama",
        description="LLM provider used to generate the answer.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve.",
    )

    document_id: str | None = Field(
        default=None,
        description="Optionally restrict retrieval to one document.",
    )


class RagSource(BaseModel):
    chunk_id: str
    document_id: str
    filename: str

    page_number: int | None = Field(
        default=None,
        ge=1,
        description=(
            "One-based source page number. "
            "None is returned for legacy indexed chunks."
        ),
    )

    chunk_index: int

    relevance_score: float

    text_preview: str    


class RagChatResponse(BaseModel):
    conversation_id: str
    question: str
    retrieval_query: str
    answer: str
    provider: str
    embedding_model: str
    retrieved_chunk_count: int
    sources: list[RagSource]
    status: str