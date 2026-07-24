import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import documents as documents_module
from app.main import app


client = TestClient(app)


def create_indexed_document(
    directory: Path,
    document_id: str,
) -> tuple[Path, Path]:
    stored_filename = (
        f"{document_id}_security-policy.pdf"
    )

    metadata = {
        "document_id": document_id,
        "original_filename": (
            "security-policy.pdf"
        ),
        "stored_filename": stored_filename,
        "content_type": "application/pdf",
        "size_bytes": 4096,
        "indexing": {
            "status": "indexed",
            "page_count": 2,
            "chunk_count": 5,
            "stored_chunk_count": 5,
            "embedding_model": "old-model",
            "embedding_dimensions": 384,
            "collection_name": "documents",
            "indexed_at": (
                "2026-07-20T10:00:00+00:00"
            ),
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

    document_path.write_bytes(
        b"temporary PDF test content"
    )

    return metadata_path, document_path


def get_indexing_result() -> dict:
    return {
        "page_count": 4,
        "extracted_character_count": 8500,
        "chunk_count": 20,
        "stored_chunk_count": 20,
        "embedding_model": "nomic-embed-text",
        "embedding_dimensions": 768,
    }


def test_reindex_document_replaces_vectors_and_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    monkeypatch.setattr(
        documents_module.settings,
        "chroma_collection_name",
        "documents",
    )

    metadata_path, document_path = (
        create_indexed_document(
            directory=tmp_path,
            document_id="document-1",
        )
    )

    with (
        patch(
            "app.api.documents."
            "delete_document_chunks"
        ) as mocked_delete,
        patch(
            "app.api.documents.index_document",
            return_value=get_indexing_result(),
        ) as mocked_index,
    ):
        response = client.post(
            "/api/documents/document-1/reindex"
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["document_id"] == "document-1"
    assert (
        payload["filename"]
        == "security-policy.pdf"
    )
    assert payload["page_count"] == 4
    assert (
        payload["extracted_character_count"]
        == 8500
    )
    assert payload["chunk_count"] == 20
    assert payload["stored_chunk_count"] == 20
    assert (
        payload["embedding_model"]
        == "nomic-embed-text"
    )
    assert payload["embedding_dimensions"] == 768
    assert payload["collection_name"] == "documents"
    assert payload["status"] == "reindexed"

    mocked_delete.assert_called_once_with(
        document_id="document-1"
    )

    mocked_index.assert_called_once_with(
        document_id="document-1",
        file_path=document_path,
        original_filename="security-policy.pdf",
        content_type="application/pdf",
    )

    updated_metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    indexing = updated_metadata["indexing"]

    assert indexing["status"] == "indexed"
    assert indexing["page_count"] == 4
    assert indexing["chunk_count"] == 20
    assert indexing["stored_chunk_count"] == 20
    assert (
        indexing["embedding_model"]
        == "nomic-embed-text"
    )
    assert indexing["embedding_dimensions"] == 768
    assert indexing["collection_name"] == "documents"
    assert indexing["indexed_at"] is not None
    assert indexing["reindexed_at"] is not None


def test_reindex_deletes_old_chunks_before_indexing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    create_indexed_document(
        directory=tmp_path,
        document_id="document-2",
    )

    operation_order = []

    def record_delete(
        document_id: str,
    ) -> None:
        operation_order.append(
            ("delete", document_id)
        )

    def record_index(**kwargs):
        operation_order.append(
            ("index", kwargs["document_id"])
        )
        return get_indexing_result()

    with (
        patch(
            "app.api.documents."
            "delete_document_chunks",
            side_effect=record_delete,
        ),
        patch(
            "app.api.documents.index_document",
            side_effect=record_index,
        ),
    ):
        response = client.post(
            "/api/documents/document-2/reindex"
        )

    assert response.status_code == 200

    assert operation_order == [
        ("delete", "document-2"),
        ("index", "document-2"),
    ]


def test_reindex_unknown_document_returns_not_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    with (
        patch(
            "app.api.documents."
            "delete_document_chunks"
        ) as mocked_delete,
        patch(
            "app.api.documents."
            "index_document"
        ) as mocked_index,
    ):
        response = client.post(
            "/api/documents/unknown/reindex"
        )

    assert response.status_code == 404
    mocked_delete.assert_not_called()
    mocked_index.assert_not_called()


def test_reindex_missing_uploaded_file_returns_not_found(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    _, document_path = (
        create_indexed_document(
            directory=tmp_path,
            document_id="missing-file",
        )
    )

    document_path.unlink()

    with (
        patch(
            "app.api.documents."
            "delete_document_chunks"
        ) as mocked_delete,
        patch(
            "app.api.documents."
            "index_document"
        ) as mocked_index,
    ):
        response = client.post(
            "/api/documents/missing-file/reindex"
        )

    assert response.status_code == 404
    mocked_delete.assert_not_called()
    mocked_index.assert_not_called()


def test_reindex_stops_when_vector_deletion_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        documents_module.settings,
        "upload_directory",
        str(tmp_path),
    )

    create_indexed_document(
        directory=tmp_path,
        document_id="document-3",
    )

    with (
        patch(
            "app.api.documents."
            "delete_document_chunks",
            side_effect=RuntimeError(
                "vector deletion failed"
            ),
        ),
        patch(
            "app.api.documents."
            "index_document"
        ) as mocked_index,
    ):
        response = client.post(
            "/api/documents/document-3/reindex"
        )

    assert response.status_code == 500
    mocked_index.assert_not_called()