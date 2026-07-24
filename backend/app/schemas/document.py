from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int
    status: str


class DocumentExtractionResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    page_count: int
    character_count: int
    text: str
    status: str

class DocumentChunkResponse(BaseModel):
    chunk_id: str
    index: int
    text: str
    character_count: int


class DocumentChunkingResponse(BaseModel):
    document_id: str
    filename: str
    original_character_count: int
    cleaned_character_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    chunks: list[DocumentChunkResponse]
    status: str


class DocumentIndexingResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    extracted_character_count: int
    chunk_count: int
    stored_chunk_count: int
    embedding_model: str
    embedding_dimensions: int
    collection_name: str
    status: str

class DocumentListItem(BaseModel):
    """
    Summary information for one uploaded document.
    """

    document_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int

    page_count: int | None = None
    chunk_count: int | None = None
    stored_chunk_count: int | None = None

    embedding_model: str | None = None
    collection_name: str | None = None

    uploaded_at: datetime
    indexed_at: datetime | None = None

    status: str


class DocumentListResponse(BaseModel):
    """
    Response containing all uploaded documents.
    """

    total: int
    documents: list[DocumentListItem] = Field(
        default_factory=list
    )

class DocumentDetailResponse(BaseModel):
    """
    Detailed metadata and indexing statistics for one document.
    """

    document_id: str
    original_filename: str
    stored_filename: str
    content_type: str
    size_bytes: int

    file_exists: bool

    page_count: int | None = None
    chunk_count: int | None = None
    stored_chunk_count: int | None = None

    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    collection_name: str | None = None

    uploaded_at: datetime
    indexed_at: datetime | None = None

    status: str

class DocumentDeleteResponse(BaseModel):
    """
    Result of deleting an uploaded document and its vector chunks.
    """

    document_id: str
    filename: str
    deleted_file: bool
    deleted_metadata: bool
    deleted_chunks: bool
    status: str