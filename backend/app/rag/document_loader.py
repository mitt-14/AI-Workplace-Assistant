import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import (
    DocumentExtractionError,
    EmptyDocumentTextError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractedPage:
    """
    Text extracted from one document page.

    TXT files are represented as a single page with page_number=1.
    """

    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedDocument:
    """
    Structured text extracted from an uploaded document.
    """

    pages: list[ExtractedPage]
    total_pages: int

    @property
    def full_text(self) -> str:
        """
        Return all extracted pages as one text value.

        This property preserves compatibility with code that still
        expects one combined document string.
        """

        return "\n\n".join(
            page.text
            for page in self.pages
        ).strip()


def extract_pdf_pages(
    file_path: Path,
) -> ExtractedDocument:
    """
    Extract readable PDF pages while preserving page numbers.
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

    extracted_pages: list[ExtractedPage] = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
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

        if not cleaned_text:
            logger.warning(
                "PDF page contains no extractable text: "
                "path=%s page=%s",
                file_path,
                page_number,
            )
            continue

        extracted_pages.append(
            ExtractedPage(
                page_number=page_number,
                text=cleaned_text,
            )
        )

    if not extracted_pages:
        raise EmptyDocumentTextError()

    extracted_character_count = sum(
        len(page.text)
        for page in extracted_pages
    )

    logger.info(
        "PDF pages extracted successfully: "
        "path=%s total_pages=%s readable_pages=%s "
        "characters=%s",
        file_path,
        len(reader.pages),
        len(extracted_pages),
        extracted_character_count,
    )

    return ExtractedDocument(
        pages=extracted_pages,
        total_pages=len(reader.pages),
    )


def extract_txt_pages(
    file_path: Path,
) -> ExtractedDocument:
    """
    Extract a plain-text document as one logical page.
    """

    try:
        text = file_path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:
        try:
            text = file_path.read_text(
                encoding="latin-1"
            )

        except (UnicodeDecodeError, OSError) as exc:
            logger.exception(
                "Failed to decode text file: path=%s",
                file_path,
            )

            raise DocumentExtractionError(
                "The text file uses an unsupported "
                "character encoding."
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
        "TXT text extracted successfully: "
        "path=%s characters=%s",
        file_path,
        len(cleaned_text),
    )

    return ExtractedDocument(
        pages=[
            ExtractedPage(
                page_number=1,
                text=cleaned_text,
            )
        ],
        total_pages=1,
    )


def extract_document_pages(
    file_path: Path,
    content_type: str,
) -> ExtractedDocument:
    """
    Extract structured, page-aware document content.
    """

    if content_type == "application/pdf":
        return extract_pdf_pages(
            file_path
        )

    if content_type == "text/plain":
        return extract_txt_pages(
            file_path
        )

    raise DocumentExtractionError(
        "No text extractor is available for content type: "
        f"{content_type}"
    )


# ------------------------------------------------------------------
# Backward-compatible functions
# ------------------------------------------------------------------

def extract_pdf_text(
    file_path: Path,
) -> tuple[str, int]:
    """
    Extract PDF text using the original return format.

    New indexing code should use extract_pdf_pages() instead.
    """

    extracted_document = extract_pdf_pages(
        file_path
    )

    return (
        extracted_document.full_text,
        extracted_document.total_pages,
    )


def extract_txt_text(
    file_path: Path,
) -> tuple[str, int]:
    """
    Extract TXT text using the original return format.

    New indexing code should use extract_txt_pages() instead.
    """

    extracted_document = extract_txt_pages(
        file_path
    )

    return (
        extracted_document.full_text,
        extracted_document.total_pages,
    )


def extract_document_text(
    file_path: Path,
    content_type: str,
) -> tuple[str, int]:
    """
    Preserve the original extraction API.

    New indexing code should use extract_document_pages().
    """

    extracted_document = extract_document_pages(
        file_path=file_path,
        content_type=content_type,
    )

    return (
        extracted_document.full_text,
        extracted_document.total_pages,
    )