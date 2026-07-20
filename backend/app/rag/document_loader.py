import logging
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import (
    DocumentExtractionError,
    EmptyDocumentTextError,
)

logger = logging.getLogger(__name__)


def extract_pdf_text(file_path: Path) -> tuple[str, int]:
    """
    Extract text from every readable page of a PDF.

    Returns:
        A tuple containing:
        - extracted text;
        - total number of PDF pages.
    """

    try:
        reader = PdfReader(str(file_path))
    except (PdfReadError, OSError, ValueError) as exc:
        logger.exception(
            "Failed to open PDF: path=%s",
            file_path,
        )

        raise DocumentExtractionError(
            "The PDF could not be opened or may be corrupted."
        ) from exc

    extracted_pages: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            logger.exception(
                "Failed to extract PDF page: path=%s page=%s",
                file_path,
                page_number,
            )
            continue

        cleaned_text = page_text.strip()

        if cleaned_text:
            extracted_pages.append(
                f"--- Page {page_number} ---\n{cleaned_text}"
            )

    full_text = "\n\n".join(extracted_pages).strip()

    if not full_text:
        raise EmptyDocumentTextError()

    logger.info(
        "PDF text extracted successfully: path=%s pages=%s characters=%s",
        file_path,
        len(reader.pages),
        len(full_text),
    )

    return full_text, len(reader.pages)


def extract_txt_text(file_path: Path) -> tuple[str, int]:
    """
    Extract text from a UTF-8 plain-text document.
    """

    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="latin-1")
        except (UnicodeDecodeError, OSError) as exc:
            logger.exception(
                "Failed to decode text file: path=%s",
                file_path,
            )

            raise DocumentExtractionError(
                "The text file uses an unsupported character encoding."
            ) from exc

    except OSError as exc:
        logger.exception(
            "Failed to read text file: path=%s",
            file_path,
        )

        raise DocumentExtractionError(
            "The text file could not be read."
        ) from exc

    cleaned_text = text.strip()

    if not cleaned_text:
        raise EmptyDocumentTextError()

    logger.info(
        "TXT text extracted successfully: path=%s characters=%s",
        file_path,
        len(cleaned_text),
    )

    return cleaned_text, 1


def extract_document_text(
    file_path: Path,
    content_type: str,
) -> tuple[str, int]:
    """
    Select the appropriate extraction method based on content type.
    """

    if content_type == "application/pdf":
        return extract_pdf_text(file_path)

    if content_type == "text/plain":
        return extract_txt_text(file_path)

    raise DocumentExtractionError(
        f"No text extractor is available for content type: {content_type}"
    )