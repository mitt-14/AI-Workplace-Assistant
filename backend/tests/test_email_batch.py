import asyncio

from app.schemas.email_analysis import BatchEmailAnalysisRequest, BatchEmailItem
from app.services import email_analyzer


def test_batch_analysis_collects_results(monkeypatch):
    async def fake_analyze(request):
        from app.schemas.email_analysis import EmailAnalysisResponse
        return EmailAnalysisResponse(
            analysis_id="id",
            provider="ollama",
            model="fake",
            processing_time_seconds=0.1,
            analysis_strategy="llm_structured",
            classification="general",
            priority="medium",
            sentiment="neutral",
            summary="Summary",
            key_points=[],
            tasks=[],
            deadlines=[],
            entities={},
            risks=[],
            suggested_reply=None,
            confidence=0.8,
        )

    monkeypatch.setattr(email_analyzer, "analyze_email", fake_analyze)
    response = asyncio.run(email_analyzer.analyze_email_batch(
        BatchEmailAnalysisRequest(
            emails=[
                BatchEmailItem(email_id="1", body="First"),
                BatchEmailItem(email_id="2", body="Second"),
            ]
        )
    ))
    assert response.total == 2
    assert response.succeeded == 2
    assert response.failed == 0
