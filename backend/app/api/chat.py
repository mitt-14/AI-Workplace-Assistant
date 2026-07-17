from fastapi import APIRouter, HTTPException
from app.ai.llm_provider import get_model

router = APIRouter()


@router.post("/chat")
def chat(
    message: str,
    provider: str = "ollama"
):

    try:
        model = get_model(provider)

        response = model.invoke(message)

        return {
            "provider": provider,
            "answer": response.content
        }

    except Exception as e:
        print("ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )