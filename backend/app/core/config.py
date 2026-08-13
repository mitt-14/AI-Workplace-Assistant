from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Workplace Assistant"
    app_version: str = "0.11.0"
    environment: str = "development"
    log_level: str = "INFO"

    default_llm_provider: str = "ollama"

    ollama_model: str = "llama3.1"
    ollama_base_url: str = "http://localhost:11434"

    embedding_model: str = "embeddinggemma"

    chroma_directory: str = "chroma_db"
    chroma_collection_name: str = "workplace_documents"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    upload_directory: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_file_types: str = "application/pdf,text/plain"

    # Phase 8: AI Document Analyzer
    document_analysis_directory: str = "data/document_analyses"
    document_analysis_chunk_characters: int = 18000
    document_analysis_chunk_overlap_characters: int = 300
    document_analysis_max_chunks: int = 10
    document_analysis_concurrency: int = 2
    document_analysis_use_llm_synthesis: bool = False
    document_analysis_cache_enabled: bool = True

    # Phase 9: AI Email Assistant
    email_analysis_batch_concurrency: int = 2

    # Phase 10: AI Meeting Assistant
    meeting_analysis_max_characters: int = 30000

    # Phase 11: Local Workflow Automation
    workflow_database_path: str = "data/workflows.db"

    conversation_database_path: str = "data/conversations.db"
    maximum_conversation_messages: int = 10

    chunk_size: int = 1000
    chunk_overlap: int = 200

    default_search_results: int = 3
    maximum_search_results: int = 10
    minimum_relevance_score: float = 0.44

    hybrid_semantic_weight: float = 0.7
    hybrid_keyword_weight: float = 0.3

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
