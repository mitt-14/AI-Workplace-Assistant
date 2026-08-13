from fastapi import APIRouter

from app.agents.agent_service import (
    run_agent,
)
from app.agents.tool_registry import (
    list_agent_tools,
)
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentToolListResponse,
)


router = APIRouter(
    prefix="/agents",
    tags=["AI Agents"],
)


@router.get(
    "/tools",
    response_model=AgentToolListResponse,
    summary="List tools available to the local AI agent",
)
async def get_agent_tools() -> AgentToolListResponse:
    tools = list_agent_tools()

    return AgentToolListResponse(
        total=len(
            tools
        ),
        tools=tools,
    )


@router.post(
    "/run",
    response_model=AgentResponse,
    summary="Run a multi-step AI workplace agent",
)
async def run_agent_endpoint(
    request: AgentRequest,
) -> AgentResponse:
    return await run_agent(
        request
    )
