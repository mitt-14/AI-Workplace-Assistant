from fastapi.testclient import TestClient

from app.api import agents
from app.main import app
from app.schemas.agent import (
    AgentPlan,
    AgentResponse,
)


client = TestClient(app)


def test_agent_tools_endpoint():
    response = client.get(
        "/api/agents/tools"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] >= 8

    names = {
        tool["name"]
        for tool in payload["tools"]
    }

    assert "analyze_document" in names
    assert "analyze_email" in names
    assert "analyze_meeting" in names
    assert "python_utility" in names


def test_agent_run_endpoint(
    monkeypatch,
):
    async def fake_run_agent(
        request,
    ):
        return AgentResponse(
            run_id="run-1",
            instruction=request.instruction,
            provider="ollama",
            model="fake",
            plan_strategy="llm_structured",
            plan=AgentPlan(
                goal=request.instruction,
                steps=[],
            ),
            executions=[],
            final_answer="Done",
            completed_steps=0,
            failed_steps=0,
            processing_time_seconds=0.01,
            status="completed",
        )

    monkeypatch.setattr(
        agents,
        "run_agent",
        fake_run_agent,
    )

    response = client.post(
        "/api/agents/run",
        json={
            "instruction": "Show me tasks",
            "provider": "ollama",
        },
    )

    assert response.status_code == 200
    assert response.json()[
        "final_answer"
    ] == "Done"
