from fastapi import FastAPI
from app.api.chat import router

app = FastAPI()


app.include_router(router)


@app.get("/")
def home():

    return {
        "status":"AI Assistant Running"
    }