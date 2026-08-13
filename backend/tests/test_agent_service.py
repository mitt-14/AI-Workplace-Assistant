import asyncio
import json

from app.agents import agent_service
from app.schemas.agent import AgentRequest


class FakePlannerResponse:
    content = json.dumps(
        {
            "goal": "Review stored tasks",
            "steps": [
                {
                    "step": 1,
                    "tool": "internal_api",
                    "arguments": {
                        "operation": "list_tasks"
                    },
                    "purpose": "Read stored tasks",
                }
            ],
        }
    )


class FakeFinalResponse:
    content = "There is one pending security task."


class FakeModel:
    model = "fake-model"

    def __init__(self):
        self.calls = 0

    async def ainvoke(
        self,
        prompt: str,
    ):
        self.calls += 1

        if self.calls == 1:
            return FakePlannerResponse()

        return FakeFinalResponse()


def test_agent_executes_planned_tool(
    monkeypatch,
):
    model = FakeModel()

    monkeypatch.setattr(
        agent_service,
        "get_model",
        lambda provider: model,
    )

    async def fake_tool(
        name,
        arguments,
    ):
        assert name == "internal_api"

        return {
            "count": 1,
            "items": [
                {
                    "title": "Security report"
                }
            ],
        }

    monkeypatch.setattr(
        agent_service,
        "execute_agent_tool",
        fake_tool,
    )

    response = asyncio.run(
        agent_service.run_agent(
            AgentRequest(
                instruction=(
                    "Show me my stored tasks."
                ),
                provider="ollama",
            )
        )
    )

    assert response.status == "completed"
    assert response.completed_steps == 1
    assert response.failed_steps == 0
    assert response.plan_strategy == "llm_structured"
    assert "pending security task" in response.final_answer.lower()


def test_agent_uses_deterministic_fallback_when_plan_is_invalid(
    monkeypatch,
):
    class InvalidModel:
        model = "fake-model"
        calls = 0

        async def ainvoke(
            self,
            prompt: str,
        ):
            self.calls += 1

            if self.calls == 1:
                return type(
                    "R",
                    (),
                    {"content": "not-json"},
                )()

            return type(
                "R",
                (),
                {"content": "Tasks retrieved."},
            )()

    monkeypatch.setattr(
        agent_service,
        "get_model",
        lambda provider: InvalidModel(),
    )

    async def fake_tool(
        name,
        arguments,
    ):
        return {
            "count": 0,
            "items": [],
        }

    monkeypatch.setattr(
        agent_service,
        "execute_agent_tool",
        fake_tool,
    )

    response = asyncio.run(
        agent_service.run_agent(
            AgentRequest(
                instruction="List my tasks",
                provider="ollama",
            )
        )
    )

    assert (
        response.plan_strategy
        == "deterministic_fallback"
    )
    assert response.status == "completed"
