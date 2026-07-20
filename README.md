# AI Workplace Assistant

An AI-powered workplace assistant built using FastAPI, Ollama, Gemini and LangChain.

## Features

- Local LLM inference using Ollama
- Cloud LLM support using Gemini
- Multiple model provider architecture
- FastAPI REST API

## Current Version

**v0.2.0**

### Completed
- ✅ Phase 1: Document Processing & Indexing
- ✅ Phase 2: Semantic Search & RAG Chat

### Next
- 🚧 Phase 3: Conversation Memory
- 🚧 Multi-document Chat
- 🚧 Frontend

## Architecture


User
 |
FastAPI
 |
LLM Provider
 |
-----------------
|               |
Ollama        Gemini


## Tech Stack

Backend:
- Python
- FastAPI
- LangChain

AI:
- Ollama
- Gemini API

Database:
- ChromaDB (coming soon)


## Run locally


Create environment:

python -m venv .aiass


Install:

pip install -r requirements.txt


Start server:

uvicorn app.main:app --reload

