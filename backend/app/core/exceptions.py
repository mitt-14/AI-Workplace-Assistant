class ApplicationError(Exception):
    """
    Base exception for expected application-level errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "APPLICATION_ERROR",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

        super().__init__(message)


class InvalidProviderError(ApplicationError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Unsupported LLM provider: {provider}",
            status_code=400,
            error_code="INVALID_PROVIDER",
        )


class LLMServiceError(ApplicationError):
    def __init__(
        self,
        message: str = "The language model service is currently unavailable.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="LLM_SERVICE_ERROR",
        )

class UnsupportedFileTypeError(ApplicationError):
    def __init__(self, content_type: str) -> None:
        super().__init__(
            message=f"Unsupported file type: {content_type}",
            status_code=415,
            error_code="UNSUPPORTED_FILE_TYPE",
        )


class FileTooLargeError(ApplicationError):
    def __init__(self, maximum_size_mb: int) -> None:
        super().__init__(
            message=f"The uploaded file exceeds the {maximum_size_mb} MB limit.",
            status_code=413,
            error_code="FILE_TOO_LARGE",
        )


class EmptyFileError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="The uploaded file is empty.",
            status_code=400,
            error_code="EMPTY_FILE",
        )

class DocumentNotFoundError(ApplicationError):
    def __init__(self, document_id: str) -> None:
        super().__init__(
            message=f"Document not found: {document_id}",
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
        )


class DocumentExtractionError(ApplicationError):
    def __init__(
        self,
        message: str = "Text could not be extracted from the document.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="DOCUMENT_EXTRACTION_ERROR",
        )


class EmptyDocumentTextError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message=(
                "No readable text was found in the document. "
                "The file may be empty or image-based."
            ),
            status_code=422,
            error_code="EMPTY_DOCUMENT_TEXT",
        )


class EmbeddingServiceError(ApplicationError):
    def __init__(
        self,
        message: str = "The embedding service is unavailable.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="EMBEDDING_SERVICE_ERROR",
        )


class DocumentIndexingError(ApplicationError):
    def __init__(
        self,
        message: str = "The document could not be indexed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="DOCUMENT_INDEXING_ERROR",
        )


class VectorStoreError(ApplicationError):
    def __init__(
        self,
        message: str = "The vector database operation failed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="VECTOR_STORE_ERROR",
        )

class SemanticSearchError(ApplicationError):
    def __init__(
        self,
        message: str = "Semantic search failed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="SEMANTIC_SEARCH_ERROR",
        )

class ConversationNotFoundError(ApplicationError):
    def __init__(
        self,
        conversation_id: str,
    ) -> None:
        super().__init__(
            message=(
                f"Conversation '{conversation_id}' "
                "was not found."
            ),
            error_code="CONVERSATION_NOT_FOUND",
            status_code=404,
        )