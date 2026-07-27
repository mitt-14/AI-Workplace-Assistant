from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import DocumentExtractionError, EmptyDocumentTextError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedDocument:
    pages: list[ExtractedPage]
    total_pages: int

    @property
    def text(self) -> str:
        return "\n\n".join(
            f"--- Page {page.page_number} ---\n{page.text}"
            for page in self.pages
            if page.text.strip()
        ).strip()


def _extract_pdf_pages(file_path: Path) -> ExtractedDocument:
    try:
        reader = PdfReader(str(file_path))
    except (PdfReadError, OSError, ValueError) as exc:
        logger.exception("Failed to open PDF: path=%s", file_path)
        raise DocumentExtractionError(
            "The PDF could not be opened or may be corrupted."
        ) from exc

    pages: list[ExtractedPage] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = (page.extract_text() or "").strip()
        except Exception:
            logger.exception(
                "Failed to extract PDF page: path=%s page=%s",
                file_path,
                page_number,
            )
            continue

        if page_text:
            pages.append(ExtractedPage(page_number=page_number, text=page_text))

    if not pages:
        raise EmptyDocumentTextError()

    return ExtractedDocument(pages=pages, total_pages=len(reader.pages))


def _extract_txt_pages(file_path: Path) -> ExtractedDocument:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="latin-1")
        except (UnicodeDecodeError, OSError) as exc:
            logger.exception("Failed to decode text file: path=%s", file_path)
            raise DocumentExtractionError(
                "The text file uses an unsupported character encoding."
            ) from exc
    except OSError as exc:
        logger.exception("Failed to read text file: path=%s", file_path)
        raise DocumentExtractionError("The text file could not be read.") from exc

    text = text.strip()
    if not text:
        raise EmptyDocumentTextError()

    return ExtractedDocument(
        pages=[ExtractedPage(page_number=1, text=text)],
        total_pages=1,
    )


def extract_document_pages(file_path: Path, content_type: str) -> ExtractedDocument:
    if content_type == "application/pdf":
        extracted = _extract_pdf_pages(file_path)
    elif content_type == "text/plain":
        extracted = _extract_txt_pages(file_path)
    else:
        raise DocumentExtractionError(
            f"No text extractor is available for content type: {content_type}"
        )

    logger.info(
        "Document text extracted: path=%s pages=%s readable_pages=%s characters=%s",
        file_path,
        extracted.total_pages,
        len(extracted.pages),
        len(extracted.text),
    )
    return extracted


# Backward-compatible functions used by the upload/indexing code.
def extract_pdf_text(file_path: Path) -> tuple[str, int]:
    extracted = _extract_pdf_pages(file_path)
    return extracted.text, extracted.total_pages


def extract_txt_text(file_path: Path) -> tuple[str, int]:
    extracted = _extract_txt_pages(file_path)
    return extracted.text, extracted.total_pages


def extract_document_text(file_path: Path, content_type: str) -> tuple[str, int]:
    extracted = extract_document_pages(file_path, content_type)
    return extracted.text, extracted.total_pages
