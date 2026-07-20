import logging
import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.exceptions import EmptyDocumentTextError

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """
    Represents one section of a processed document.
    """

    chunk_id: str
    index: int
    text: str
    character_count: int


def clean_document_text(text: str) -> str:
    """
    Normalize extracted document text before chunking.

    The function:
    - normalizes line endings;
    - removes null characters;
    - removes unnecessary spaces;
    - limits excessive blank lines;
    - preserves paragraph boundaries.
    """

    if not text or not text.strip():
        raise EmptyDocumentTextError()

    cleaned_text = text.replace("\r\n", "\n")
    cleaned_text = cleaned_text.replace("\r", "\n")
    cleaned_text = cleaned_text.replace("\x00", "")

    # Replace repeated spaces and tabs with one space.
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)

    # Remove spaces before new lines.
    cleaned_text = re.sub(r" +\n", "\n", cleaned_text)

    # Limit three or more new lines to two.
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    cleaned_text = cleaned_text.strip()

    if not cleaned_text:
        raise EmptyDocumentTextError()

    return cleaned_text


def split_document_text(
    text: str,
    document_id: str,
) -> list[TextChunk]:
    """
    Clean and split document text into overlapping chunks.
    """

    cleaned_text = clean_document_text(text)

    if settings.chunk_overlap >= settings.chunk_size:
        raise ValueError(
            "CHUNK_OVERLAP must be smaller than CHUNK_SIZE."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    split_texts = splitter.split_text(cleaned_text)

    chunks = [
        TextChunk(
            chunk_id=f"{document_id}_chunk_{index}",
            index=index,
            text=chunk_text,
            character_count=len(chunk_text),
        )
        for index, chunk_text in enumerate(split_texts)
        if chunk_text.strip()
    ]

    if not chunks:
        raise EmptyDocumentTextError()

    logger.info(
        "Document split successfully: document_id=%s chunks=%s "
        "chunk_size=%s overlap=%s",
        document_id,
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )

    return chunks