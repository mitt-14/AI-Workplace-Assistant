from enum import Enum

from pydantic import BaseModel, Field, model_validator


class MeetingPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class MeetingDecision(BaseModel):
    decision: str = Field(min_length=1)
    owner: str | None = None
    rationale: str | None = None


class MeetingActionItem(BaseModel):
    task: str = Field(min_length=1)
    owner: str | None = None
    deadline: str | None = None
    normalized_deadline: str | None = Field(
        default=None,
        description="ISO-8601 date or datetime when confidently resolvable.",
    )
    priority: MeetingPriority = MeetingPriority.medium


class MeetingDeadline(BaseModel):
    text: str = Field(min_length=1)
    normalized_date: str | None = Field(
        default=None,
        description="ISO-8601 date or datetime when confidently resolvable.",
    )
    context: str | None = None


class MeetingAnalysisContent(BaseModel):
    summary: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    decisions: list[MeetingDecision] = Field(default_factory=list)
    action_items: list[MeetingActionItem] = Field(default_factory=list)
    participants: list[str] = Field(default_factory=list)
    deadlines: list[MeetingDeadline] = Field(default_factory=list)
    follow_up_items: list[str] = Field(default_factory=list)
    follow_up_email: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class MeetingAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    transcript: str = Field(min_length=1, max_length=200_000)
    provider: str | None = Field(default=None, examples=["ollama"])
    generate_follow_up_email: bool = True
    follow_up_email_style: str = Field(
        default="professional",
        min_length=1,
        max_length=100,
    )


class MeetingAnalysisResponse(MeetingAnalysisContent):
    analysis_id: str
    title: str | None = None
    provider: str
    model: str | None = None
    processing_time_seconds: float
    analysis_strategy: str
    transcript_character_count: int
    analyzed_character_count: int
    was_truncated: bool


class MeetingFollowUpRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    transcript: str | None = Field(default=None, max_length=200_000)
    summary: str | None = Field(default=None, max_length=20_000)
    decisions: list[MeetingDecision] = Field(default_factory=list)
    action_items: list[MeetingActionItem] = Field(default_factory=list)
    participants: list[str] = Field(default_factory=list)
    provider: str | None = Field(default=None, examples=["ollama"])
    style: str = Field(default="professional", min_length=1, max_length=100)
    sender_name: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def require_meeting_context(self) -> "MeetingFollowUpRequest":
        if not any(
            [
                self.transcript and self.transcript.strip(),
                self.summary and self.summary.strip(),
                self.decisions,
                self.action_items,
            ]
        ):
            raise ValueError(
                "Provide transcript, summary, decisions, or action_items."
            )
        return self


class MeetingFollowUpResponse(BaseModel):
    email: str
    provider: str
    model: str | None = None
    style: str
    processing_time_seconds: float
