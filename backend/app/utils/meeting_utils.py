import json
import re
from collections.abc import Iterable
from typing import Any


_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*(.*?)```",
    re.IGNORECASE | re.DOTALL,
)

_SPEAKER_RE = re.compile(
    r"(?m)^\s*([A-Za-z][A-Za-z0-9 ._'’-]{0,60})\s*:\s+"
)

_DEADLINE_RE = re.compile(
    r"\b("
    r"today|tomorrow|tonight|"
    r"next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week)|"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|"
    r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|"
    r"\d{4}-\d{2}-\d{2}"
    r")\b",
    re.IGNORECASE,
)


def response_to_text(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(
                block.get("text"),
                str,
            ):
                parts.append(block["text"])
            else:
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    parts.append(text)

        return "\n".join(parts).strip()

    return str(content).strip()


def extract_json_object(
    text: str,
) -> dict[str, Any] | None:
    candidates = [text.strip()]

    fenced = _JSON_FENCE_RE.search(text)
    if fenced:
        candidates.insert(
            0,
            fenced.group(1).strip(),
        )

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        candidates.append(
            text[start : end + 1]
        )

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue

        if isinstance(value, dict):
            return value

    return None


def unique_strings(
    values: Iterable[str],
    limit: int | None = None,
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        clean = " ".join(
            str(value).split()
        ).strip(" -•\t\r\n")

        if not clean:
            continue

        key = clean.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(clean)

        if (
            limit is not None
            and len(result) >= limit
        ):
            break

    return result


def extract_speakers(
    transcript: str,
) -> list[str]:
    return unique_strings(
        _SPEAKER_RE.findall(transcript),
        limit=50,
    )


def extract_deadline_phrases(
    transcript: str,
) -> list[str]:
    return unique_strings(
        match.group(0)
        for match in _DEADLINE_RE.finditer(
            transcript
        )
    )


def truncate_transcript(
    transcript: str,
    maximum_characters: int,
) -> tuple[str, bool]:
    clean = transcript.strip()

    if len(clean) <= maximum_characters:
        return clean, False

    truncated = clean[:maximum_characters]

    boundary = max(
        truncated.rfind("\n"),
        truncated.rfind(". "),
        truncated.rfind("? "),
        truncated.rfind("! "),
    )

    if boundary >= maximum_characters // 2:
        truncated = truncated[: boundary + 1]

    return truncated.strip(), True
