import logging
import re
import time
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from app.ai.llm_provider import get_model
from app.core.config import settings
from app.core.exceptions import (
    LLMServiceError,
    MeetingAnalysisError,
)
from app.prompts.meeting_analysis_prompt import (
    build_meeting_analysis_prompt,
    build_meeting_follow_up_prompt,
)
from app.schemas.meeting_analysis import (
    MeetingActionItem,
    MeetingAnalysisContent,
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    MeetingDeadline,
    MeetingDecision,
    MeetingFollowUpRequest,
    MeetingFollowUpResponse,
    MeetingPriority,
)
from app.utils.meeting_utils import (
    extract_deadline_phrases,
    extract_json_object,
    extract_speakers,
    response_to_text,
    truncate_transcript,
    unique_strings,
)

logger = logging.getLogger(__name__)

_ACTION_RE = re.compile(
    r"\b("
    r"please|need to|needs to|must|should|"
    r"will|action item|todo|to-do|"
    r"follow up|prepare|send|review|complete|"
    r"update|create|schedule|investigate"
    r")\b",
    re.IGNORECASE,
)

_DECISION_RE = re.compile(
    r"\b("
    r"decided|decision|agreed|approved|"
    r"we will|will proceed|"
    r"postpone|cancelled|canceled"
    r")\b",
    re.IGNORECASE,
)

_URGENT_RE = re.compile(
    r"\b(urgent|asap|immediately|critical|today)\b",
    re.IGNORECASE,
)

_HIGH_RE = re.compile(
    r"\b(deadline|blocked|security|incident|breach|production)\b",
    re.IGNORECASE,
)


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

        if isinstance(value, str):
            return value

    return None


async def _invoke(
    model: Any,
    prompt: str,
    provider: str,
    stage: str,
) -> str:
    try:
        response = await model.ainvoke(
            prompt
        )
        text = response_to_text(
            response
        )

    except Exception as exc:
        logger.exception(
            "Meeting LLM request failed: "
            "provider=%s stage=%s",
            provider,
            stage,
        )

        raise LLMServiceError(
            "The meeting-analysis language model request failed."
        ) from exc

    if not text:
        raise LLMServiceError(
            "The meeting-analysis language model "
            "returned an empty response."
        )

    return text


def _split_statements(
    transcript: str,
) -> list[str]:
    statements = [
        " ".join(part.split())
        for part in re.split(
            r"(?<=[.!?])\s+|\n+",
            transcript,
        )
        if part.strip()
    ]

    return unique_strings(
        statements,
        limit=40,
    )


def _priority_for_text(
    text: str,
) -> MeetingPriority:
    if _URGENT_RE.search(text):
        return MeetingPriority.urgent

    if _HIGH_RE.search(text):
        return MeetingPriority.high

    return MeetingPriority.medium


def _speaker_from_statement(
    statement: str,
) -> str | None:
    match = re.match(
        r"^\s*([A-Za-z][A-Za-z0-9 ._'’-]{0,60})\s*:",
        statement,
    )

    if not match:
        return None

    return match.group(1).strip()


def _heuristic_analysis(
    request: MeetingAnalysisRequest,
    transcript: str,
) -> MeetingAnalysisContent:
    statements = _split_statements(
        transcript
    )

    participants = extract_speakers(
        transcript
    )

    deadlines = [
        MeetingDeadline(
            text=value,
            context=None,
        )
        for value in extract_deadline_phrases(
            transcript
        )[:10]
    ]

    decisions: list[MeetingDecision] = []

    for statement in statements:
        if _DECISION_RE.search(
            statement
        ):
            decisions.append(
                MeetingDecision(
                    decision=statement[:1000],
                )
            )

        if len(decisions) >= 10:
            break

    action_items: list[
        MeetingActionItem
    ] = []

    for statement in statements:
        if not _ACTION_RE.search(
            statement
        ):
            continue

        owner = _speaker_from_statement(
            statement
        )

        matching_deadlines = (
            extract_deadline_phrases(
                statement
            )
        )

        action_items.append(
            MeetingActionItem(
                task=statement[:1000],
                owner=owner,
                deadline=(
                    matching_deadlines[0]
                    if matching_deadlines
                    else None
                ),
                priority=_priority_for_text(
                    statement
                ),
            )
        )

        if len(action_items) >= 12:
            break

    key_points = unique_strings(
        statements,
        limit=8,
    )

    summary = (
        " ".join(
            key_points[:3]
        )[:1200]
        or "Meeting transcript received for review."
    )

    follow_up_items = unique_strings(
        [
            item.task
            for item in action_items
        ],
        limit=8,
    )

    return MeetingAnalysisContent(
        summary=summary,
        key_points=key_points,
        decisions=decisions,
        action_items=action_items,
        participants=participants,
        deadlines=deadlines,
        follow_up_items=follow_up_items,
        follow_up_email=None,
        confidence=0.35,
    )


def _merge_deterministic_data(
    content: MeetingAnalysisContent,
    transcript: str,
) -> None:
    content.participants = unique_strings(
        [
            *content.participants,
            *extract_speakers(
                transcript
            ),
        ],
        limit=50,
    )

    existing_deadlines = {
        deadline.text.casefold()
        for deadline in content.deadlines
    }

    for deadline in extract_deadline_phrases(
        transcript
    ):
        if (
            deadline.casefold()
            in existing_deadlines
        ):
            continue

        content.deadlines.append(
            MeetingDeadline(
                text=deadline,
            )
        )

        existing_deadlines.add(
            deadline.casefold()
        )


async def analyze_meeting(
    request: MeetingAnalysisRequest,
) -> MeetingAnalysisResponse:
    started = time.perf_counter()
    provider = _provider(
        request.provider
    )

    analyzed_transcript, was_truncated = (
        truncate_transcript(
            request.transcript,
            settings.meeting_analysis_max_characters,
        )
    )

    model = get_model(
        provider
    )

    raw = await _invoke(
        model,
        build_meeting_analysis_prompt(
            request,
            analyzed_transcript,
        ),
        provider,
        "analysis",
    )

    payload = extract_json_object(
        raw
    )

    strategy = "llm_structured"

    if payload is None:
        logger.warning(
            "Meeting analysis returned no JSON; "
            "using deterministic fallback"
        )

        content = _heuristic_analysis(
            request,
            analyzed_transcript,
        )

        strategy = (
            "deterministic_fallback"
        )

    else:
        try:
            content = (
                MeetingAnalysisContent
                .model_validate(
                    payload
                )
            )

            _merge_deterministic_data(
                content,
                analyzed_transcript,
            )

        except ValidationError as exc:
            logger.warning(
                "Meeting analysis JSON "
                "validation failed: %s",
                exc,
            )

            content = _heuristic_analysis(
                request,
                analyzed_transcript,
            )

            strategy = (
                "deterministic_fallback"
            )

    if (
        request.generate_follow_up_email
        and not content.follow_up_email
    ):
        follow_up = (
            await generate_meeting_follow_up(
                MeetingFollowUpRequest(
                    title=request.title,
                    transcript=None,
                    summary=content.summary,
                    decisions=content.decisions,
                    action_items=content.action_items,
                    participants=content.participants,
                    provider=provider,
                    style=(
                        request
                        .follow_up_email_style
                    ),
                ),
                model=model,
            )
        )

        content.follow_up_email = (
            follow_up.email
        )

    return MeetingAnalysisResponse(
        analysis_id=str(
            uuid4()
        ),
        title=request.title,
        provider=provider,
        model=_model_name(
            model
        ),
        processing_time_seconds=round(
            time.perf_counter()
            - started,
            3,
        ),
        analysis_strategy=strategy,
        transcript_character_count=len(
            request.transcript
        ),
        analyzed_character_count=len(
            analyzed_transcript
        ),
        was_truncated=was_truncated,
        **content.model_dump(),
    )


async def generate_meeting_follow_up(
    request: MeetingFollowUpRequest,
    model: Any | None = None,
) -> MeetingFollowUpResponse:
    started = time.perf_counter()
    provider = _provider(
        request.provider
    )

    selected_model = (
        model
        or get_model(
            provider
        )
    )

    raw = await _invoke(
        selected_model,
        build_meeting_follow_up_prompt(
            request
        ),
        provider,
        "follow_up",
    )

    email = (
        raw.strip()
        .strip("`")
        .strip()
    )

    if not email:
        raise MeetingAnalysisError(
            "The meeting follow-up email "
            "could not be generated."
        )

    return MeetingFollowUpResponse(
        email=email,
        provider=provider,
        model=_model_name(
            selected_model
        ),
        style=request.style,
        processing_time_seconds=round(
            time.perf_counter()
            - started,
            3,
        ),
    )
