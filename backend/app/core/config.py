from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    OLLAMA_URL:str="http://localhost:11434"

    OLLAMA_MODEL:str="llama3.1"

    GEMINI_API_KEY:str | None=None

    DEFAULT_MODEL:str="ollama"


    class Config:

        env_file=".env"



settings = Settings()