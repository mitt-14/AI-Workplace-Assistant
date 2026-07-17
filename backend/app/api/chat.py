from fastapi import APIRouter

from app.schemas.chat import ChatRequest

from app.ai.llm_provider import get_model


router=APIRouter()



@router.post("/chat")
def chat(
    request:ChatRequest
):


    model=get_model(
        request.provider
    )


    response=model.invoke(
        request.message
    )


    return {

        "provider":request.provider,

        "answer":response.content

    }