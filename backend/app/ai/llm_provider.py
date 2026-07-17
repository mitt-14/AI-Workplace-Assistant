from app.ai.ollama_model import get_ollama_model
from app.ai.gemini_model import get_gemini_model


def get_model(provider):

    if provider == "ollama":
        return get_ollama_model()

    elif provider == "gemini":
        return get_gemini_model()

    else:
        raise Exception(
            "Unknown AI provider"
        )