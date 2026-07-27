from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class EmailClassification(str, Enum):
    hr = "hr"
    finance = "finance"
    legal = "legal"
    support = "support"
    complaint = "complaint"
    sales = "sales"
    meeting = "meeting"
    technical = "technical"
    personal = "personal"
    spam = "spam"
    phishing = "phishing"
    general = "general"


class EmailPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class EmailSentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class ReplyStyle(str, Enum):
    professional = "professional"
    friendly = "friendly"
    formal = "formal"
    concise = "concise"
    detailed = "detailed"
    custom = "custom"


class EmailRiskType(str, Enum):
    phishing = "phishing"
    spam = "spam"
    suspicious_link = "suspicious_link"
    credential_theft = "credential_theft"
    payment_fraud = "payment_fraud"
    malicious_attachment = "malicious_attachment"
    social_engineering = "social_engineering"
    privacy = "privacy"
    other = "other"


class EmailRiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EmailInput(BaseModel):
    subject: str | None = Field(default=None, max_length=500)
    sender: str | None = Field(default=None, max_length=500)
    recipients: list[str] = Field(default_factory=list, max_length=50)
    body: str = Field(min_length=1, max_length=100_000)


class EmailTask(BaseModel):
    task: str = Field(min_length=1)
    owner: str | None = None
    deadline: str | None = None
    priority: EmailPriority = EmailPriority.medium


class EmailDeadline(BaseModel):
    text: str = Field(min_length=1)
    normalized_date: str | None = Field(
        default=None,
        description="ISO-8601 date or datetime when confidently resolvable.",
    )
    context: str | None = None


class EmailEntities(BaseModel):
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    email_addresses: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    monetary_amounts: list[str] = Field(default_factory=list)


class EmailRisk(BaseModel):
    type: EmailRiskType
    severity: EmailRiskSeverity
    description: str = Field(min_length=1)
    evidence: str | None = None


class EmailAnalysisContent(BaseModel):
    classification: EmailClassification = EmailClassification.general
    priority: EmailPriority = EmailPriority.medium
    sentiment: EmailSentiment = EmailSentiment.neutral
    summary: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    tasks: list[EmailTask] = Field(default_factory=list)
    deadlines: list[EmailDeadline] = Field(default_factory=list)
    entities: EmailEntities = Field(default_factory=EmailEntities)
    risks: list[EmailRisk] = Field(default_factory=list)
    suggested_reply: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EmailAnalysisRequest(EmailInput):
    provider: str | None = Field(default=None, examples=["ollama"])
    generate_reply: bool = True
    reply_style: ReplyStyle = ReplyStyle.professional
    custom_reply_instructions: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def validate_custom_style(self) -> "EmailAnalysisRequest":
        if self.reply_style == ReplyStyle.custom and not self.custom_reply_instructions:
            raise ValueError(
                "custom_reply_instructions is required when reply_style is custom."
            )
        return self


class EmailAnalysisResponse(EmailAnalysisContent):
    analysis_id: str
    provider: str
    model: str | None = None
    processing_time_seconds: float
    analysis_strategy: str


class EmailReplyRequest(EmailInput):
    provider: str | None = Field(default=None, examples=["ollama"])
    style: ReplyStyle = ReplyStyle.professional
    custom_instructions: str | None = Field(default=None, max_length=2_000)
    sender_name: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_custom_style(self) -> "EmailReplyRequest":
        if self.style == ReplyStyle.custom and not self.custom_instructions:
            raise ValueError("custom_instructions is required when style is custom.")
        return self


class EmailReplyResponse(BaseModel):
    reply: str
    provider: str
    model: str | None = None
    style: ReplyStyle
    processing_time_seconds: float


class BatchEmailItem(EmailInput):
    email_id: str = Field(min_length=1, max_length=200)


class BatchEmailAnalysisRequest(BaseModel):
    emails: Annotated[list[BatchEmailItem], Field(min_length=1, max_length=20)]
    provider: str | None = Field(default=None, examples=["ollama"])
    generate_reply: bool = False
    reply_style: ReplyStyle = ReplyStyle.professional


class BatchEmailAnalysisResult(BaseModel):
    email_id: str
    analysis: EmailAnalysisResponse | None = None
    error: str | None = None


class BatchEmailAnalysisResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BatchEmailAnalysisResult]
    processing_time_seconds: float
