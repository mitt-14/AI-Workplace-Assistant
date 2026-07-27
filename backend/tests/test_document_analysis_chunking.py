import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.rag.document_loader import ExtractedDocument, ExtractedPage
from app.services import document_analyzer as analyzer_module

client = TestClient(app)


def _write_document(directory: Path) -> None:
    metadata = {
        "document_id": "doc-long",
        "original_filename": "handbook.pdf",
        "stored_filename": "doc-long_handbook.pdf",
        "content_type": "application/pdf",
    }
    (directory / "doc-long.json").write_text(json.dumps(metadata), encoding="utf-8")
    (directory / "doc-long_handbook.pdf").write_bytes(b"placeholder")


def _content(summary: str, page: int) -> dict:
    return {
        "executive_summary": summary,
        "key_points": [f"Point from page {page}"],
        "risks": [],
        "action_items": [],
        "recommendations": [],
    }


def test_long_document_is_analyzed_in_multiple_chunks(tmp_path: Path, monkeypatch) -> None:
    upload_dir = tmp_path / "uploads"
    analysis_dir = tmp_path / "analyses"
    upload_dir.mkdir()
    _write_document(upload_dir)

    monkeypatch.setattr(analyzer_module.settings, "upload_directory", str(upload_dir))
    monkeypatch.setattr(analyzer_module.settings, "document_analysis_directory", str(analysis_dir))
    monkeypatch.setattr(analyzer_module.settings, "document_analysis_chunk_characters", 1200)
    monkeypatch.setattr(analyzer_module.settings, "document_analysis_chunk_overlap_characters", 100)
    monkeypatch.setattr(analyzer_module.settings, "document_analysis_max_chunks", 10)

    extracted = ExtractedDocument(
        pages=[
            ExtractedPage(page_number=1, text="A" * 1000),
            ExtractedPage(page_number=2, text="B" * 1000),
            ExtractedPage(page_number=3, text="C" * 1000),
        ],
        total_pages=3,
    )

    responses = [
        SimpleNamespace(content=json.dumps(_content("Chunk one", 1))),
        SimpleNamespace(content=json.dumps(_content("Chunk two", 2))),
        SimpleNamespace(content=json.dumps(_content("Chunk three", 3))),
    ]
    model = SimpleNamespace(model="test-model", ainvoke=AsyncMock(side_effect=responses))

    with (
        patch("app.services.document_analyzer.extract_document_pages", return_value=extracted),
        patch("app.services.document_analyzer.get_model", return_value=model),
    ):
        response = client.post(
            "/api/document-analysis/doc-long/analyze",
            json={"provider": "ollama"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["chunk_count"] == 3
    assert payload["analyzed_chunk_count"] == 3
    assert payload["analysis_strategy"] == "chunked_parallel_deterministic_merge"
    assert payload["was_truncated"] is False
    assert payload["executive_summary"]
    assert model.ainvoke.await_count == 3
