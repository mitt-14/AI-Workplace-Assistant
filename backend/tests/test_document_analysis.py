import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.services import document_analyzer as analyzer_module
from app.main import app
from app.rag.document_loader import ExtractedDocument, ExtractedPage

client = TestClient(app)


def write_document(tmp_path: Path) -> None:
    metadata = {
        "document_id": "doc-1",
        "original_filename": "policy.txt",
        "stored_filename": "doc-1_policy.txt",
        "content_type": "text/plain",
        "size_bytes": 20,
    }
    (tmp_path / "doc-1.json").write_text(json.dumps(metadata))
    (tmp_path / "doc-1_policy.txt").write_text("Example policy")


def test_analyze_document_returns_and_saves_structured_analysis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    upload_dir = tmp_path / "uploads"
    analysis_dir = tmp_path / "analyses"
    upload_dir.mkdir()
    write_document(upload_dir)

    monkeypatch.setattr(analyzer_module.settings, "upload_directory", str(upload_dir))
    monkeypatch.setattr(
        analyzer_module.settings,
        "document_analysis_directory",
        str(analysis_dir),
    )

    extracted = ExtractedDocument(
        pages=[ExtractedPage(page_number=1, text="Remote work is allowed.")],
        total_pages=1,
    )

    response_json = {
        "executive_summary": "The policy permits remote work.",
        "key_points": ["Remote work is allowed."],
        "risks": [],
        "action_items": [],
        "recommendations": ["Communicate the policy clearly."],
    }

    mock_model = SimpleNamespace(
        model="test-model",
        ainvoke=AsyncMock(
            return_value=SimpleNamespace(content=json.dumps(response_json))
        ),
    )

    with (
        patch(
            "app.services.document_analyzer.extract_document_pages",
            return_value=extracted,
        ),
        patch(
            "app.services.document_analyzer.get_model",
            return_value=mock_model,
        ),
    ):
        response = client.post(
            "/api/document-analysis/doc-1/analyze",
            json={"provider": "ollama"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document_id"] == "doc-1"
    assert payload["provider"] == "ollama"
    assert payload["executive_summary"] == "The policy permits remote work."
    assert payload["status"] == "completed"
    assert (analysis_dir / f"{payload['analysis_id']}.json").exists()


def test_get_missing_analysis_returns_404(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        analyzer_module.settings,
        "document_analysis_directory",
        str(tmp_path),
    )

    response = client.get("/api/document-analysis/missing")

    assert response.status_code == 404
    assert response.json()["error"] == "DOCUMENT_ANALYSIS_NOT_FOUND"
