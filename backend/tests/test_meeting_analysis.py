import asyncio

from app.schemas.meeting_analysis import (
    MeetingAnalysisRequest,
)
from app.services import meeting_analyzer


class FakeResponse:
    content = """{
      "summary": "The team reviewed the security release.",
      "key_points": [
        "Security review must finish before deployment"
      ],
      "decisions": [
        {
          "decision": "Production deployment is postponed.",
          "owner": null,
          "rationale": "Security review is incomplete."
        }
      ],
      "action_items": [
        {
          "task": "Complete the vulnerability report",
          "owner": "Miten",
          "deadline": "Friday",
          "normalized_deadline": null,
          "priority": "high"
        }
      ],
      "participants": ["Alice", "Miten"],
      "deadlines": [
        {
          "text": "Friday",
          "normalized_date": null,
          "context": "Vulnerability report"
        }
      ],
      "follow_up_items": [
        "Complete the vulnerability report"
      ],
      "follow_up_email": "Thanks everyone. Miten will complete the report by Friday.",
      "confidence": 0.94
    }"""


class FakeModel:
    model = "fake-model"

    async def ainvoke(
        self,
        prompt: str,
    ):
        return FakeResponse()


def test_analyze_meeting_returns_structured_response(
    monkeypatch,
):
    monkeypatch.setattr(
        meeting_analyzer,
        "get_model",
        lambda provider: FakeModel(),
    )

    response = asyncio.run(
        meeting_analyzer.analyze_meeting(
            MeetingAnalysisRequest(
                title="Security meeting",
                transcript=(
                    "Alice: We decided to postpone production deployment. "
                    "Miten: I will complete the vulnerability report by Friday."
                ),
                provider="ollama",
            )
        )
    )

    assert (
        response.analysis_strategy
        == "llm_structured"
    )
    assert response.model == "fake-model"
    assert "Alice" in response.participants
    assert "Miten" in response.participants
    assert len(response.decisions) == 1
    assert len(response.action_items) == 1
    assert (
        response.action_items[0].owner
        == "Miten"
    )


def test_invalid_json_uses_deterministic_fallback(
    monkeypatch,
):
    class InvalidModel:
        model = "fake-model"

        async def ainvoke(
            self,
            prompt: str,
        ):
            return type(
                "R",
                (),
                {"content": "Not JSON"},
            )()

    monkeypatch.setattr(
        meeting_analyzer,
        "get_model",
        lambda provider: InvalidModel(),
    )

    response = asyncio.run(
        meeting_analyzer.analyze_meeting(
            MeetingAnalysisRequest(
                title="Weekly meeting",
                transcript=(
                    "Alice: We decided to postpone deployment.\n"
                    "Miten: I will send the report tomorrow."
                ),
                generate_follow_up_email=False,
            )
        )
    )

    assert (
        response.analysis_strategy
        == "deterministic_fallback"
    )
    assert "Alice" in response.participants
    assert "Miten" in response.participants
    assert response.confidence == 0.35
    assert response.decisions
    assert response.action_items
