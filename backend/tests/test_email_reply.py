import asyncio

from app.schemas.email_analysis import EmailReplyRequest, ReplyStyle
from app.services import email_analyzer


class FakeModel:
    model = "fake-model"

    async def ainvoke(self, prompt: str):
        return type("R", (), {"content": "Thank you for your message. I will review it today."})()


def test_generate_email_reply(monkeypatch):
    monkeypatch.setattr(email_analyzer, "get_model", lambda provider: FakeModel())
    response = asyncio.run(email_analyzer.generate_email_reply(
        EmailReplyRequest(
            subject="Proposal",
            body="Please review the proposal.",
            style=ReplyStyle.professional,
        )
    ))
    assert response.reply.startswith("Thank you")
    assert response.style == ReplyStyle.professional
