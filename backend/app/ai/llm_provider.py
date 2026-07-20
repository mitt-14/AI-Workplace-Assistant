import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.ai.gemini_model import get_gemini_model
from app.ai.ollama_model import get_ollama_model
from app.core.exceptions import InvalidProviderError

logger = logging.getLogger(__name__)


def get_model(provider: str) -> BaseChatModel:
    """
    Return the configured language model for the selected provider.
    """

    normalized_provider = provider.strip().lower()

    logger.info(
        "Selecting LLM provider: %s",
        normalized_provider,
    )

    if normalized_provider == "ollama":
        return get_ollama_model()

    if normalized_provider == "gemini":
        return get_gemini_model()

    logger.warning(
        "Unsupported LLM provider requested: %s",
        normalized_provider,
    )

    raise InvalidProviderError(normalized_provider)