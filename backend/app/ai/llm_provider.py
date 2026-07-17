from app.ai.ollama_model import get_ollama_model

from app.ai.gemini_model import get_gemini_model



def get_model(provider:str):


    if provider=="gemini":

        return get_gemini_model()


    return get_ollama_model()