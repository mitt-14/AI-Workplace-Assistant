from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class ConversationCreateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Optional conversation title.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_title = value.strip()

        if not cleaned_title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        return cleaned_title

class ConversationRenameRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="New conversation title.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned_title = value.strip()

        if not cleaned_title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        return cleaned_title


class ConversationResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class ConversationRenameResponse(
    ConversationResponse
):
    status: str

class ConversationListResponse(BaseModel):
    conversation_count: int
    conversations: list[ConversationResponse]
    status: str

class ConversationSearchResponse(BaseModel):
    query: str
    result_count: int
    total_count: int
    limit: int
    offset: int
    conversations: list[ConversationResponse]
    status: str

class ConversationMessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    provider: str | None = None
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: list[ConversationMessageResponse]
    status: str


class ConversationDeleteResponse(BaseModel):
    conversation_id: str
    status: str