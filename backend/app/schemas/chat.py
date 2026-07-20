from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The message sent to the AI assistant.",
    )

    provider: Literal["ollama", "gemini"] | None = Field(
        default=None,
        description="LLM provider used to generate the response.",
    )


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str