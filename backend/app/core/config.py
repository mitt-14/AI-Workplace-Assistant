from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workplace Assistant"
    app_version: str = "0.2.0"
    environment: str = "development"
    log_level: str = "INFO"

    default_llm_provider: str = "ollama"

    ollama_model: str = "llama3.1"
    ollama_base_url: str = "http://localhost:11434"

    embedding_model: str = "embeddinggemma"
    ollama_base_url: str = "http://localhost:11434"

    chroma_directory: str = "chroma_db"
    chroma_collection_name: str = "workplace_documents"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    upload_directory: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_file_types: str = "application/pdf,text/plain"

    conversation_database_path: str = "data/conversations.db"
    maximum_conversation_messages: int = 10

    chunk_size: int = 1000
    chunk_overlap: int = 200

    default_search_results: int = 3
    maximum_search_results: int = 10

    minimum_relevance_score: float = 0.44
    
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()