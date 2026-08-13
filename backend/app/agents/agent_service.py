from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from app.ai.llm_provider import get_model
from app.agents.tool_registry import (
    execute_agent_tool,
    list_agent_tools,
)
from app.core.config import settings
from app.core.exceptions import (
    AgentExecutionError,
    LLMServiceError,
)
from app.schemas.agent import (
    AgentPlan,
    AgentPlanStep,
    AgentRequest,
    AgentResponse,
    AgentToolExecution,
)

logger = logging.getLogger(__name__)


def _provider(
    provider: str | None,
) -> str:
    return (
        provider
        or settings.default_llm_provider
    ).strip().lower()


def _model_name(
    model: Any,
) -> str | None:
    for attribute in (
        "model",
        "model_name",
    ):
        value = getattr(
            model,
            attribute,
            None,
        )

        if isinstance(
            value,
            str,
        ):
            return value

    return None


def _response_text(
    response: Any,
) -> str:
    content = getattr(
        response,
        "content",
        response,
    )

    if isinstance(
        content,
        str,
    ):
        return content.strip()

    return str(
        content
    ).strip()


def _extract_json(
    text: str,
) -> dict[str, Any] | None:
    cleaned = text.strip()

    fence = re.search(
        r"```(?:json)?\s*(.*?)```",
        cleaned,
        re.IGNORECASE | re.DOTALL,
    )

    candidates = []

    if fence:
        candidates.append(
            fence.group(1).strip()
        )

    candidates.append(
        cleaned
    )

    start = cleaned.find(
        "{"
    )
    end = cleaned.rfind(
        "}"
    )

    if start >= 0 and end > start:
        candidates.append(
            cleaned[
                start : end + 1
            ]
        )

    for candidate in candidates:
        try:
            value = json.loads(
                candidate
            )
        except json.JSONDecodeError:
            continue

        if isinstance(
            value,
            dict,
        ):
            return value

    return None


def _planner_prompt(
    request: AgentRequest,
) -> str:
    tools = [
        item.model_dump(
            mode="json"
        )
        for item in list_agent_tools()
    ]

    return f"""
You are the planning component of an internal AI Workplace Assistant.

Create a short executable plan for the user's request.

Return ONLY valid JSON using exactly this shape:
{{
  "goal": "short description",
  "steps": [
    {{
      "step": 1,
      "tool": "tool_name",
      "arguments": {{}},
      "purpose": "short user-visible purpose"
    }}
  ]
}}

Rules:
- Use only tools from the supplied tool list.
- Never invent document IDs or other missing identifiers.
- Use context values when they are available.
- Do not create unnecessary steps.
- Maximum steps: {request.max_steps}.
- If no tool is necessary, return an empty steps array.
- Do not include hidden reasoning or chain-of-thought.
- For email analysis use analyze_email unless the user explicitly
  wants tasks stored, in which case use run_email_workflow.
- For document analysis use analyze_document unless the user explicitly
  wants extracted tasks stored, in which case use run_document_workflow.
- python_utility is allowlisted utility execution, not arbitrary code.
- internal_api operations are only list_tasks, list_notifications,
  and list_workflow_executions.

Available tools:
{json.dumps(tools, ensure_ascii=False)}

User instruction:
{request.instruction}

Structured context:
{json.dumps(request.context, ensure_ascii=False, default=str)}
""".strip()


def _deterministic_plan(
    request: AgentRequest,
) -> AgentPlan:
    text = request.instruction.casefold()
    context = request.context

    steps: list[
        AgentPlanStep
    ] = []

    def add(
        tool,
        arguments,
        purpose,
    ):
        if len(
            steps
        ) >= request.max_steps:
            return

        steps.append(
            AgentPlanStep(
                step=len(
                    steps
                ) + 1,
                tool=tool,
                arguments=arguments,
                purpose=purpose,
            )
        )

    if (
        "document" in text
        or "policy" in text
        or "knowledge" in text
    ):
        document_id = context.get(
            "document_id"
        )

        if (
            document_id
            and (
                "analy" in text
                or "summary" in text
                or "risk" in text
            )
        ):
            add(
                "analyze_document",
                {
                    "document_id": document_id,
                    "provider": request.provider,
                },
                "Analyze the selected document.",
            )

        elif context.get(
            "query"
        ) or request.instruction:
            add(
                "search_company_documents",
                {
                    "query": context.get(
                        "query",
                        request.instruction,
                    ),
                    "top_k": context.get(
                        "top_k",
                        5,
                    ),
                    "document_id": document_id,
                },
                "Search company knowledge.",
            )

    if (
        "email" in text
        and context.get(
            "body"
        )
    ):
        tool = (
            "run_email_workflow"
            if (
                "store" in text
                or "create task" in text
                or "save task" in text
            )
            else "analyze_email"
        )

        add(
            tool,
            {
                "subject": context.get(
                    "subject"
                ),
                "sender": context.get(
                    "sender"
                ),
                "recipients": context.get(
                    "recipients",
                    [],
                ),
                "body": context[
                    "body"
                ],
                "provider": request.provider,
            },
            "Process the supplied email.",
        )

    if (
        "meeting" in text
        and context.get(
            "transcript"
        )
    ):
        add(
            "analyze_meeting",
            {
                "title": context.get(
                    "title"
                ),
                "transcript": context[
                    "transcript"
                ],
                "provider": request.provider,
            },
            "Analyze the meeting transcript.",
        )

    if (
        "task" in text
        and not context.get(
            "body"
        )
    ):
        add(
            "internal_api",
            {
                "operation": "list_tasks",
            },
            "Read stored tasks.",
        )

    if (
        any(
            keyword in text
            for keyword in (
                "calculate",
                "calculator",
                "mean",
                "median",
                "word count",
            )
        )
        and context.get(
            "python_utility"
        )
    ):
        add(
            "python_utility",
            context[
                "python_utility"
            ],
            "Run the requested local utility.",
        )

    return AgentPlan(
        goal=request.instruction,
        steps=steps,
    )


async def _make_plan(
    request: AgentRequest,
    model: Any,
) -> tuple[
    AgentPlan,
    str,
]:
    try:
        raw = await model.ainvoke(
            _planner_prompt(
                request
            )
        )

    except Exception:
        logger.exception(
            "Agent planning LLM call failed; "
            "using deterministic planner"
        )

        return (
            _deterministic_plan(
                request
            ),
            "deterministic_fallback",
        )

    payload = _extract_json(
        _response_text(
            raw
        )
    )

    if payload is None:
        return (
            _deterministic_plan(
                request
            ),
            "deterministic_fallback",
        )

    try:
        plan = AgentPlan.model_validate(
            payload
        )

    except ValidationError:
        logger.exception(
            "Agent planner JSON validation failed"
        )

        return (
            _deterministic_plan(
                request
            ),
            "deterministic_fallback",
        )

    plan.steps = plan.steps[
        : request.max_steps
    ]

    for index, step in enumerate(
        plan.steps,
        start=1,
    ):
        step.step = index

        # Ensure the selected provider is inherited unless
        # the planner explicitly supplied one.
        if (
            "provider"
            not in step.arguments
            and step.tool
            in {
                "analyze_document",
                "analyze_email",
                "analyze_meeting",
                "run_email_workflow",
                "run_document_workflow",
            }
        ):
            step.arguments[
                "provider"
            ] = request.provider

    return (
        plan,
        "llm_structured",
    )


def _compact_result(
    value: Any,
    limit: int = 6000,
) -> str:
    text = json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )

    if len(
        text
    ) > limit:
        return (
            text[:limit]
            + "...[truncated]"
        )

    return text


async def _final_answer(
    *,
    request: AgentRequest,
    model: Any,
    executions: list[
        AgentToolExecution
    ],
) -> str:
    if not executions:
        return (
            "No tool execution was required or enough "
            "structured context was not available."
        )

    successful = [
        execution
        for execution in executions
        if execution.status
        == "completed"
    ]

    if not successful:
        return (
            "The agent could not complete the requested "
            "tool operations."
        )

    evidence = [
        {
            "tool": execution.tool,
            "purpose": execution.purpose,
            "result": execution.result,
        }
        for execution in successful
    ]

    prompt = f"""
You are the response component of an internal AI Workplace Assistant.

Answer the user's request using ONLY the completed tool results below.
Be concise and practical.
Do not invent facts.
Do not reveal hidden reasoning.
If a tool result is incomplete, say so.

User request:
{request.instruction}

Tool results:
{_compact_result(evidence)}

Return only the final user-facing answer.
""".strip()

    try:
        response = await model.ainvoke(
            prompt
        )

        answer = _response_text(
            response
        )

        if answer:
            return answer

    except Exception:
        logger.exception(
            "Agent final synthesis failed; "
            "using deterministic result summary"
        )

    parts = []

    for execution in successful:
        parts.append(
            f"{execution.tool}: "
            f"{_compact_result(execution.result, 1200)}"
        )

    return "\n\n".join(
        parts
    )


async def run_agent(
    request: AgentRequest,
) -> AgentResponse:
    started = time.perf_counter()
    provider = _provider(
        request.provider
    )

    try:
        model = get_model(
            provider
        )

    except Exception as exc:
        raise LLMServiceError(
            "The agent language model could not be initialized."
        ) from exc

    plan, strategy = await _make_plan(
        request,
        model,
    )

    executions: list[
        AgentToolExecution
    ] = []

    for step in plan.steps:
        step_started = (
            time.perf_counter()
        )

        try:
            result = await execute_agent_tool(
                step.tool,
                step.arguments,
            )

            executions.append(
                AgentToolExecution(
                    step=step.step,
                    tool=step.tool,
                    purpose=step.purpose,
                    status="completed",
                    result=result,
                    processing_time_seconds=round(
                        time.perf_counter()
                        - step_started,
                        3,
                    ),
                )
            )

        except Exception as exc:
            logger.exception(
                "Agent tool failed: "
                "step=%s tool=%s",
                step.step,
                step.tool,
            )

            executions.append(
                AgentToolExecution(
                    step=step.step,
                    tool=step.tool,
                    purpose=step.purpose,
                    status="failed",
                    error=str(
                        exc
                    ),
                    processing_time_seconds=round(
                        time.perf_counter()
                        - step_started,
                        3,
                    ),
                )
            )

            if settings.agent_stop_on_tool_error:
                break

    final_answer = await _final_answer(
        request=request,
        model=model,
        executions=executions,
    )

    completed = sum(
        execution.status
        == "completed"
        for execution in executions
    )

    failed = sum(
        execution.status
        == "failed"
        for execution in executions
    )

    if failed == 0:
        status = "completed"

    elif completed > 0:
        status = "partial"

    else:
        status = "failed"

    if (
        status == "failed"
        and plan.steps
        and not executions
    ):
        raise AgentExecutionError(
            "The agent could not execute its plan."
        )

    return AgentResponse(
        run_id=str(
            uuid4()
        ),
        instruction=request.instruction,
        provider=provider,
        model=_model_name(
            model
        ),
        plan_strategy=strategy,
        plan=plan,
        executions=executions,
        final_answer=final_answer,
        completed_steps=completed,
        failed_steps=failed,
        processing_time_seconds=round(
            time.perf_counter()
            - started,
            3,
        ),
        status=status,
    )
