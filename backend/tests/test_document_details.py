import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import documents as documents_module
from app.main import app


client = TestClient(app)


def write_document_metadata(
    directory: Path,
    document_id: str,
    *,
    filename: str = "policy.pdf",
    indexed: bool = False,
    create_file: bool = True,
    include_uploaded_at: bool = True,
) -> None:
    """
    Create document metadata and optionally create the uploaded file.
    """

    stored_filename = f"{document_id}_{filename}"

    metadata = {
        "document_id": document_id,
        "original_filename": filename,
        "stored_filename": stored_filename,
        "content_type": "application/pdf",
        "size_bytes": 4096,
    }

    if include_uploaded_at:
        metadata["uploaded_at"] = datetime.now(
            timezone.utc
        ).isoformat()

    if indexed:
        metadata["indexing"] = {
            "status": "indexed",
            "page_count": 8,
            "chunk_count": 32,
            "stored_chunk_count": 32,
            "embedding_model": "nomic-embed-text",
            "embedding_dimensions": 768,
            "collection_name": "documents",
            "indexed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    metadata_path = directory / f"{document_id}.json"

    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    if create_file:
        document_path = directory / stored_filename

        document_path.write_bytes(
            b"test document content"
        )


def test_get_uploaded_document_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_document_metadata(
        directory=tmp_path,
        document_id="uploaded-document",
        filename="employee-handbook.pdf",
        indexed=False,
    )

    response = client.get(
        "/api/documents/uploaded-document"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["document_id"]
        == "uploaded-document"
    )
    assert (
        payload["original_filename"]
        == "employee-handbook.pdf"
    )
    assert payload["content_type"] == "application/pdf"
    assert payload["size_bytes"] == 4096
    assert payload["file_exists"] is True
    assert payload["status"] == "uploaded"

    assert payload["page_count"] is None
    assert payload["chunk_count"] is None
    assert payload["stored_chunk_count"] is None
    assert payload["embedding_model"] is None
    assert payload["embedding_dimensions"] is None
    assert payload["collection_name"] is None
    assert payload["indexed_at"] is None

    assert payload["uploaded_at"] is not None


def test_get_indexed_document_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_document_metadata(
        directory=tmp_path,
        document_id="indexed-document",
        filename="security-policy.pdf",
        indexed=True,
    )

    response = client.get(
        "/api/documents/indexed-document"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["document_id"]
        == "indexed-document"
    )
    assert payload["status"] == "indexed"
    assert payload["file_exists"] is True

    assert payload["page_count"] == 8
    assert payload["chunk_count"] == 32
    assert payload["stored_chunk_count"] == 32
    assert (
        payload["embedding_model"]
        == "nomic-embed-text"
    )
    assert payload["embedding_dimensions"] == 768
    assert payload["collection_name"] == "documents"
    assert payload["indexed_at"] is not None


def test_get_document_details_reports_missing_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_document_metadata(
        directory=tmp_path,
        document_id="missing-file-document",
        filename="missing.pdf",
        indexed=True,
        create_file=False,
    )

    response = client.get(
        "/api/documents/missing-file-document"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["document_id"]
        == "missing-file-document"
    )
    assert payload["file_exists"] is False
    assert payload["status"] == "indexed"
    assert payload["chunk_count"] == 32


def test_get_document_details_uses_metadata_timestamp_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_document_metadata(
        directory=tmp_path,
        document_id="legacy-document",
        filename="legacy.pdf",
        indexed=False,
        include_uploaded_at=False,
    )

    response = client.get(
        "/api/documents/legacy-document"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["document_id"]
        == "legacy-document"
    )
    assert payload["uploaded_at"] is not None
    assert payload["status"] == "uploaded"


def test_get_document_details_returns_not_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    response = client.get(
        "/api/documents/nonexistent-document"
    )

    assert response.status_code == 404