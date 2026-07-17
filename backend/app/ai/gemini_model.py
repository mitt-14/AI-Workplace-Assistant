from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()


def get_gemini_model():

    api_key = os.getenv("GEMINI_API_KEY")

    print("Gemini key loaded:", api_key is not None)

    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.7
    )