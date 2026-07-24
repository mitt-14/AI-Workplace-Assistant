from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RetrievalMode = Literal[
    "semantic",
    "keyword",
    "hybrid",
]


class RAGRequest(BaseModel):
    """
    Request model for document-grounded question answering.
    """

    question: str = Field(
        min_length=1,
        max_length=4000,
        description=(
            "Question that should be answered using "
            "the indexed documents."
        ),
    )

    provider: str = Field(
        default="ollama",
        min_length=1,
        max_length=50,
        description="LLM provider to use.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description=(
            "Maximum number of document chunks "
            "included in the RAG context."
        ),
    )

    document_id: str | None = Field(
        default=None,
        description=(
            "Optional document ID used to restrict "
            "retrieval to one document."
        ),
    )

    document_ids: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description=(
            "Optional document IDs used to restrict retrieval "
            "to multiple selected documents."
        ),
    )

    conversation_id: str | None = Field(
        default=None,
        description=(
            "Existing conversation ID. A new conversation "
            "is created when this value is omitted."
        ),
    )

    retrieval_mode: RetrievalMode = Field(
        default="hybrid",
        description=(
            "Retrieval strategy: semantic, keyword, "
            "or hybrid."
        ),
    )


class RAGSource(BaseModel):
    """
    Citation and retrieval information for one source chunk.
    """

    chunk_id: str
    document_id: str
    filename: str

    page_number: int | None = None
    chunk_index: int | None = None
    page_chunk_index: int | None = None

    relevance_score: float | None = None
    keyword_score: float | None = None

    normalized_semantic_score: float | None = None
    normalized_keyword_score: float | None = None

    hybrid_score: float | None = None

    retrieval_methods: list[str] = Field(
        default_factory=list
    )

    text_preview: str


class RAGSearchResult(BaseModel):
    """
    Complete retrieved chunk returned for debugging and evaluation.
    """

    chunk_id: str | None = None
    document_id: str | None = None
    filename: str | None = None
    content_type: str | None = None

    page_number: int | None = None
    chunk_index: int | None = None
    page_chunk_index: int | None = None
    character_count: int | None = None

    text: str = ""

    relevance_score: float | None = None
    keyword_score: float | None = None

    normalized_semantic_score: float | None = None
    normalized_keyword_score: float | None = None

    hybrid_score: float | None = None
    semantic_weight: float | None = None
    keyword_weight: float | None = None

    retrieval_methods: list[str] = Field(
        default_factory=list
    )

class RAGMetrics(BaseModel):
    """
    Timing and quality metrics collected during
    a RAG request.
    """

    retrieval_time_ms: float

    generation_time_ms: float

    total_time_ms: float

    retrieved_chunk_count: int

    documents_retrieved: int

    average_relevance_score: float | None = None
    highest_relevance_score: float | None = None
    lowest_relevance_score: float | None = None

    average_keyword_score: float | None = None

    average_hybrid_score: float | None = None

    average_chunk_length: float | None = None

class RAGResponse(BaseModel):
    """
    Non-streaming RAG response.
    """

    conversation_id: str
    retrieval_query: str
    retrieval_mode: RetrievalMode

    answer: str

    search_results: list[RAGSearchResult] = Field(
        default_factory=list
    )

    sources: list[RAGSource] = Field(
        default_factory=list
    )

    metrics: RAGMetrics | None = None

    status: str = "completed"


class RAGStreamStartData(BaseModel):
    conversation_id: str
    question: str
    retrieval_query: str
    retrieval_mode: RetrievalMode
    provider: str


class RAGStreamSourcesData(BaseModel):
    retrieval_mode: RetrievalMode
    retrieved_chunk_count: int

    sources: list[RAGSource] = Field(
        default_factory=list
    )


class RAGStreamTokenData(BaseModel):
    content: str


class RAGStreamDoneData(BaseModel):
    conversation_id: str
    retrieval_mode: RetrievalMode
    status: str = "completed"
    metrics: RAGMetrics | None = None

class RAGStreamErrorData(BaseModel):
    conversation_id: str
    message: str


class RAGStreamEvent(BaseModel):
    """
    Generic schema representing a streaming event.

    The data structure differs depending on the event value.
    """

    event: Literal[
        "start",
        "sources",
        "token",
        "done",
        "error",
    ]

    data: dict[str, Any]

# Backward-compatible aliases for existing API imports.
RagChatRequest = RAGRequest
RagChatResponse = RAGResponse
RagSource = RAGSource

class RAGEvaluationResponse(BaseModel):
    """
    Response returned by the RAG evaluation endpoint.
    """

    question: str

    retrieval_query: str

    retrieval_mode: RetrievalMode

    search_results: list[RAGSearchResult] = Field(
        default_factory=list
    )

    sources: list[RAGSource] = Field(
        default_factory=list
    )

    metrics: RAGMetrics