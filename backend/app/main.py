from fastapi import FastAPI

from app.api.chat import router as chat_router


app = FastAPI(
    title="AI Workplace Assistant",
    version="1.0.0"
)


app.include_router(
    chat_router,
    prefix="/api"
)


@app.get("/health")
def health():

    return {
        "status":"running"
    }