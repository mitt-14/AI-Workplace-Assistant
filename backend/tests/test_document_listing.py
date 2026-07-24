import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import documents as documents_module
from app.main import app


client = TestClient(app)


def write_metadata(
    directory: Path,
    document_id: str,
    *,
    filename: str = "policy.pdf",
    indexed: bool = False,
    uploaded_at: str | None = None,
) -> None:
    """
    Create document metadata for listing tests.
    """

    metadata = {
        "document_id": document_id,
        "original_filename": filename,
        "stored_filename": f"{document_id}_{filename}",
        "content_type": "application/pdf",
        "size_bytes": 2048,
        "uploaded_at": (
            uploaded_at
            or datetime.now(timezone.utc).isoformat()
        ),
    }

    if indexed:
        metadata["indexing"] = {
            "status": "indexed",
            "page_count": 5,
            "chunk_count": 20,
            "stored_chunk_count": 20,
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


def test_list_documents_returns_empty_list(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    response = client.get("/api/documents")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 0
    assert payload["documents"] == []


def test_list_documents_returns_uploaded_document(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_metadata(
        directory=tmp_path,
        document_id="document-1",
        filename="employee-handbook.pdf",
        indexed=False,
    )

    response = client.get("/api/documents")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1

    document = payload["documents"][0]

    assert document["document_id"] == "document-1"
    assert (
        document["original_filename"]
        == "employee-handbook.pdf"
    )
    assert document["status"] == "uploaded"
    assert document["page_count"] is None
    assert document["chunk_count"] is None
    assert document["indexed_at"] is None


def test_list_documents_returns_indexed_document(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_metadata(
        directory=tmp_path,
        document_id="document-2",
        filename="security-policy.pdf",
        indexed=True,
    )

    response = client.get("/api/documents")

    assert response.status_code == 200

    payload = response.json()
    document = payload["documents"][0]

    assert payload["total"] == 1
    assert document["status"] == "indexed"
    assert document["page_count"] == 5
    assert document["chunk_count"] == 20
    assert document["stored_chunk_count"] == 20
    assert (
        document["embedding_model"]
        == "nomic-embed-text"
    )
    assert document["indexed_at"] is not None


def test_list_documents_orders_newest_first(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    write_metadata(
        directory=tmp_path,
        document_id="older-document",
        uploaded_at="2026-07-20T10:00:00+00:00",
    )

    write_metadata(
        directory=tmp_path,
        document_id="newer-document",
        uploaded_at="2026-07-24T10:00:00+00:00",
    )

    response = client.get("/api/documents")

    assert response.status_code == 200

    documents = response.json()["documents"]

    assert len(documents) == 2
    assert documents[0]["document_id"] == "newer-document"
    assert documents[1]["document_id"] == "older-document"


def test_list_documents_skips_invalid_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    valid_metadata = {
        "document_id": "valid-document",
        "original_filename": "valid.pdf",
        "stored_filename": "valid-document_valid.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024,
        "uploaded_at": (
            "2026-07-24T10:00:00+00:00"
        ),
    }

    (
        tmp_path / "valid-document.json"
    ).write_text(
        json.dumps(valid_metadata),
        encoding="utf-8",
    )

    (
        tmp_path / "broken-document.json"
    ).write_text(
        "{invalid-json",
        encoding="utf-8",
    )

    response = client.get("/api/documents")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert (
        payload["documents"][0]["document_id"]
        == "valid-document"
    )