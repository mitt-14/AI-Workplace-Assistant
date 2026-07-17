from langchain_ollama import ChatOllama


def get_ollama_model():

    return ChatOllama(
        model="llama3.1:8b",
        temperature=0.7
    )