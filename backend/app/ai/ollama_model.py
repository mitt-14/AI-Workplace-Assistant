from langchain_ollama import ChatOllama

from app.core.config import settings



def get_ollama_model():

    return ChatOllama(

        model=settings.OLLAMA_MODEL,
        
        base_url=settings.OLLAMA_URL
    
    )