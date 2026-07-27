from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    """
    Supported risk severity levels.
    """

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionItemPriority(str, Enum):
    """
    Supported action-item priority levels.
    """

    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class DocumentAnalysisRequest(BaseModel):
    """
    Request used to analyze an uploaded document.

    When provider is omitted, the application's configured default
    provider is used.
    """

    provider: str | None = Field(
        default=None,
        examples=["ollama"],
    )


class DocumentRisk(BaseModel):
    """
    One risk identified in the analyzed document.
    """

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    severity: RiskSeverity = RiskSeverity.medium

    page_numbers: list[int] = Field(
        default_factory=list,
    )


class DocumentActionItem(BaseModel):
    """
    One actionable task extracted from the document.
    """

    task: str = Field(
        min_length=1,
    )

    priority: ActionItemPriority = ActionItemPriority.medium

    owner: str | None = None
    deadline: str | None = None

    page_numbers: list[int] = Field(
        default_factory=list,
    )


class DocumentAnalysisContent(BaseModel):
    """
    Structured AI-generated document analysis.
    """

    executive_summary: str = Field(
        min_length=1,
    )

    key_points: list[str] = Field(
        default_factory=list,
    )

    risks: list[DocumentRisk] = Field(
        default_factory=list,
    )

    action_items: list[DocumentActionItem] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class DocumentAnalysisResponse(BaseModel):
    """
    Complete response returned after analyzing one document.
    """

    analysis_id: str
    document_id: str
    filename: str
    content_type: str

    provider: str
    model: str | None = None

    page_count: int
    readable_page_count: int

    original_character_count: int
    analyzed_character_count: int
    was_truncated: bool

    chunk_count: int = 1
    analyzed_chunk_count: int = 1
    analysis_strategy: str = "single_pass"
    processing_time_seconds: float | None = None
    cached: bool = False

    executive_summary: str
    key_points: list[str]

    risks: list[DocumentRisk]
    action_items: list[DocumentActionItem]
    recommendations: list[str]

    created_at: datetime
    status: str


class DocumentAnalysisListItem(BaseModel):
    """
    Summary information for one saved analysis.
    """

    analysis_id: str
    document_id: str
    filename: str
    provider: str
    created_at: datetime
    status: str


class DocumentAnalysisListResponse(BaseModel):
    """
    Response containing saved document analyses.
    """

    total: int

    analyses: list[DocumentAnalysisListItem] = Field(
        default_factory=list,
    )