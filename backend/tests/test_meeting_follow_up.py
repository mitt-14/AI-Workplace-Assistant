import asyncio

from app.schemas.meeting_analysis import (
    MeetingActionItem,
    MeetingFollowUpRequest,
)
from app.services import meeting_analyzer


class FakeModel:
    model = "fake-model"

    async def ainvoke(
        self,
        prompt: str,
    ):
        return type(
            "R",
            (),
            {
                "content": (
                    "Hi team,\n\n"
                    "Thanks for the meeting. "
                    "Miten will complete the security report by Friday.\n\n"
                    "Regards"
                )
            },
        )()


def test_generate_meeting_follow_up(
    monkeypatch,
):
    monkeypatch.setattr(
        meeting_analyzer,
        "get_model",
        lambda provider: FakeModel(),
    )

    response = asyncio.run(
        meeting_analyzer.generate_meeting_follow_up(
            MeetingFollowUpRequest(
                title="Security meeting",
                summary="The team reviewed the security release.",
                action_items=[
                    MeetingActionItem(
                        task="Complete the security report",
                        owner="Miten",
                        deadline="Friday",
                    )
                ],
                provider="ollama",
            )
        )
    )

    assert response.provider == "ollama"
    assert response.model == "fake-model"
    assert "Friday" in response.email
