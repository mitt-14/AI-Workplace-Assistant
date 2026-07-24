import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import documents as documents_module
from app.main import app


client = TestClient(app)


def create_test_document(
    directory: Path,
    document_id: str,
    *,
    filename: str = "policy.pdf",
    create_file: bool = True,
) -> tuple[Path, Path]:
    """
    Create metadata and optionally a physical uploaded file.
    """

    stored_filename = (
        f"{document_id}_{filename}"
    )

    metadata = {
        "document_id": document_id,
        "original_filename": filename,
        "stored_filename": stored_filename,
        "content_type": "application/pdf",
        "size_bytes": 1024,
        "indexing": {
            "status": "indexed",
            "page_count": 3,
            "chunk_count": 12,
            "stored_chunk_count": 12,
            "embedding_model": "nomic-embed-text",
            "embedding_dimensions": 768,
            "collection_name": "documents",
        },
    }

    metadata_path = (
        directory / f"{document_id}.json"
    )

    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    document_path = (
        directory / stored_filename
    )

    if create_file:
        document_path.write_bytes(
            b"temporary test document"
        )

    return metadata_path, document_path


def test_delete_document_removes_everything(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    metadata_path, document_path = (
        create_test_document(
            directory=tmp_path,
            document_id="document-1",
            filename="security-policy.pdf",
        )
    )

    with patch(
        "app.api.documents.delete_document_chunks"
    ) as mocked_delete_chunks:
        response = client.delete(
            "/api/documents/document-1"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["document_id"] == "document-1"
    assert (
        payload["filename"]
        == "security-policy.pdf"
    )
    assert payload["deleted_file"] is True
    assert payload["deleted_metadata"] is True
    assert payload["deleted_chunks"] is True
    assert payload["status"] == "deleted"

    assert not document_path.exists()
    assert not metadata_path.exists()

    mocked_delete_chunks.assert_called_once_with(
        document_id="document-1"
    )


def test_delete_document_when_file_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    metadata_path, document_path = (
        create_test_document(
            directory=tmp_path,
            document_id="document-2",
            filename="missing.pdf",
            create_file=False,
        )
    )

    assert not document_path.exists()
    assert metadata_path.exists()

    with patch(
        "app.api.documents.delete_document_chunks"
    ) as mocked_delete_chunks:
        response = client.delete(
            "/api/documents/document-2"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["deleted_file"] is False
    assert payload["deleted_metadata"] is True
    assert payload["deleted_chunks"] is True
    assert payload["status"] == "deleted"

    assert not metadata_path.exists()

    mocked_delete_chunks.assert_called_once_with(
        document_id="document-2"
    )


def test_delete_unknown_document_returns_not_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    with patch(
        "app.api.documents.delete_document_chunks"
    ) as mocked_delete_chunks:
        response = client.delete(
            "/api/documents/unknown-document"
        )

    assert response.status_code == 404

    mocked_delete_chunks.assert_not_called()


def test_delete_document_uses_safe_stored_filename(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    outside_file = (
        tmp_path.parent / "outside-file.txt"
    )

    outside_file.write_text(
        "must not be deleted",
        encoding="utf-8",
    )

    document_id = "unsafe-document"

    metadata = {
        "document_id": document_id,
        "original_filename": "unsafe.txt",
        "stored_filename": "../outside-file.txt",
        "content_type": "text/plain",
        "size_bytes": 19,
    }

    metadata_path = (
        tmp_path / f"{document_id}.json"
    )

    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    with patch(
        "app.api.documents.delete_document_chunks"
    ):
        response = client.delete(
            f"/api/documents/{document_id}"
        )

    assert response.status_code == 200

    # The file outside the upload directory must remain.
    assert outside_file.exists()
    assert (
        outside_file.read_text(
            encoding="utf-8"
        )
        == "must not be deleted"
    )

    assert not metadata_path.exists()