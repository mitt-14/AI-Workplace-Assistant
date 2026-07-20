import logging

from fastapi import APIRouter

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.exceptions import ApplicationError, LLMServiceError
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with the AI assistant",
)
async def chat(request: ChatRequest) -> ChatResponse:
    provider = request.provider or settings.default_llm_provider

    logger.info(
        "Received chat request using provider=%s",
        provider,
    )

    try:
        model = get_model(provider)

        result = await model.ainvoke(request.message)

        response_text = (
            result.content
            if hasattr(result, "content")
            else str(result)
        )

        model_name = getattr(
            model,
            "model",
            getattr(model, "model_name", "unknown"),
        )

        logger.info(
            "Chat response generated successfully using provider=%s",
            provider,
        )

        return ChatResponse(
            response=response_text,
            provider=provider,
            model=str(model_name),
        )

    except ApplicationError:
        raise

    except Exception as exc:
        logger.exception(
            "LLM request failed using provider=%s",
            provider,
        )

        raise LLMServiceError(
            message=(
                f"The {provider} service could not generate a response. "
                "Check whether the model service and configuration are available."
            )
        ) from exc