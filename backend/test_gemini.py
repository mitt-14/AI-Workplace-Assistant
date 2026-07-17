from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


response = model.invoke(
    "Explain RAG in one sentence"
)


print(response.content)