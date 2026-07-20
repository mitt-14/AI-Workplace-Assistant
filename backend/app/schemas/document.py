from pydantic import BaseModel


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
    status: str#

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