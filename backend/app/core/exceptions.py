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

class DocumentAnalysisError(ApplicationError):
    def __init__(
        self,
        message: str = "The document could not be analyzed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="DOCUMENT_ANALYSIS_ERROR",
        )


class DocumentAnalysisParseError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message=(
                "The language model returned an invalid document "
                "analysis response."
            ),
            status_code=502,
            error_code="DOCUMENT_ANALYSIS_PARSE_ERROR",
        )


class DocumentAnalysisNotFoundError(ApplicationError):
    def __init__(self, analysis_id: str) -> None:
        super().__init__(
            message=f"Document analysis not found: {analysis_id}",
            status_code=404,
            error_code="DOCUMENT_ANALYSIS_NOT_FOUND",
        )


class EmailAnalysisError(ApplicationError):
    def __init__(
        self,
        message: str = "The email could not be analyzed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="EMAIL_ANALYSIS_ERROR",
        )


class EmailAnalysisParseError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="The language model returned an invalid email analysis response.",
            status_code=502,
            error_code="EMAIL_ANALYSIS_PARSE_ERROR",
        )


class MeetingAnalysisError(ApplicationError):
    def __init__(
        self,
        message: str = "The meeting could not be analyzed.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="MEETING_ANALYSIS_ERROR",
        )


class MeetingAnalysisParseError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message=(
                "The language model returned an invalid "
                "meeting analysis response."
            ),
            status_code=502,
            error_code="MEETING_ANALYSIS_PARSE_ERROR",
        )


class TaskNotFoundError(ApplicationError):
    def __init__(self, task_id: str) -> None:
        super().__init__(message=f"Task not found: {task_id}", status_code=404, error_code="TASK_NOT_FOUND")

class NotificationNotFoundError(ApplicationError):
    def __init__(self, notification_id: str) -> None:
        super().__init__(message=f"Notification not found: {notification_id}", status_code=404, error_code="NOTIFICATION_NOT_FOUND")


class AgentExecutionError(ApplicationError):
    def __init__(
        self,
        message: str = "The AI agent could not complete the request.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="AGENT_EXECUTION_ERROR",
        )


class AgentPlanError(ApplicationError):
    def __init__(
        self,
        message: str = "The AI agent could not create a valid plan.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="AGENT_PLAN_ERROR",
        )



class AuthenticationError(ApplicationError):
    def __init__(
        self,
        message: str = "Authentication is required.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
        )


class EmailAlreadyRegisteredError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            message="An account with this email already exists.",
            status_code=409,
            error_code="EMAIL_ALREADY_REGISTERED",
        )
