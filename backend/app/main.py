import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.document_analysis import router as document_analysis_router
from app.api.documents import router as documents_router
from app.api.email_analysis import router as email_analysis_router
from app.api.meeting_analysis import router as meeting_analysis_router
from app.api.notifications import router as notifications_router
from app.api.rag import router as rag_router
from app.api.search import router as search_router
from app.api.tasks import router as tasks_router
from app.api.workflows import router as workflows_router
from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.logging_config import configure_logging
from app.core.workflow_store import initialize_workflow_database
from app.core.user_store import initialize_user_database

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_workflow_database()
    initialize_user_database()

    logger.info(
        "Starting %s version %s in %s mode",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    yield

    logger.info(
        "Shutting down %s",
        settings.app_name,
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApplicationError)
async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    logger.warning(
        "Application error: code=%s path=%s message=%s",
        exc.error_code,
        request.url.path,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Request validation failed: path=%s errors=%s",
        request.url.path,
        exc.errors(),
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": (
                "The submitted request contains invalid data."
            ),
            "path": request.url.path,
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unexpected server error: path=%s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": (
                "An unexpected server error occurred."
            ),
            "path": request.url.path,
        },
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Check application health",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(document_analysis_router, prefix="/api")
app.include_router(email_analysis_router, prefix="/api")
app.include_router(meeting_analysis_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
