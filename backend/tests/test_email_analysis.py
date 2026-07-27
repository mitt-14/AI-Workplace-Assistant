import asyncio

from app.schemas.email_analysis import EmailAnalysisRequest
from app.services import email_analyzer


class FakeResponse:
    content = '''{
      "classification": "support",
      "priority": "high",
      "sentiment": "negative",
      "summary": "The customer cannot access their account.",
      "key_points": ["Login fails after password reset"],
      "tasks": [{"task": "Investigate the account", "owner": null, "deadline": "today", "priority": "high"}],
      "deadlines": [{"text": "today", "normalized_date": null, "context": "Investigate today"}],
      "entities": {"people": [], "organizations": [], "email_addresses": [], "phone_numbers": [], "urls": [], "monetary_amounts": []},
      "risks": [],
      "suggested_reply": "We are investigating the issue.",
      "confidence": 0.92
    }'''


class FakeModel:
    model = "fake-model"

    async def ainvoke(self, prompt: str):
        return FakeResponse()


def test_analyze_email_returns_structured_response(monkeypatch):
    monkeypatch.setattr(email_analyzer, "get_model", lambda provider: FakeModel())
    response = asyncio.run(email_analyzer.analyze_email(
        EmailAnalysisRequest(
            subject="Login problem",
            sender="customer@example.com",
            body="I cannot login after resetting my password. Please investigate today.",
            provider="ollama",
        )
    ))
    assert response.classification.value == "support"
    assert response.priority.value == "high"
    assert response.model == "fake-model"
    assert response.entities.email_addresses == ["customer@example.com"]
    assert response.analysis_strategy == "llm_structured"


def test_invalid_llm_json_uses_fallback(monkeypatch):
    class InvalidModel:
        model = "fake-model"
        async def ainvoke(self, prompt: str):
            return type("R", (), {"content": "Not JSON"})()

    monkeypatch.setattr(email_analyzer, "get_model", lambda provider: InvalidModel())
    response = asyncio.run(email_analyzer.analyze_email(
        EmailAnalysisRequest(
            subject="Urgent invoice",
            body="Please review this invoice immediately.",
            generate_reply=False,
        )
    ))
    assert response.analysis_strategy == "deterministic_fallback"
    assert response.priority.value == "urgent"
