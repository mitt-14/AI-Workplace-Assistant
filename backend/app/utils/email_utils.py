import json
import re
from collections.abc import Iterable
from typing import Any

from app.schemas.email_analysis import EmailEntities


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s<>\]\[\)\(\"']+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_MONEY_RE = re.compile(
    r"(?:€|\$|£|₹)\s?\d[\d.,]*|\b\d[\d.,]*\s?(?:EUR|USD|GBP|INR)\b",
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
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            else:
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()


def extract_json_object(text: str) -> dict[str, Any] | None:
    candidates = [text.strip()]
    fenced = _JSON_FENCE_RE.search(text)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def unique_strings(values: Iterable[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = " ".join(str(value).split()).strip(" -•\t\r\n")
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if limit is not None and len(result) >= limit:
            break
    return result


def extract_deterministic_entities(
    subject: str | None,
    sender: str | None,
    recipients: list[str],
    body: str,
) -> EmailEntities:
    text = "\n".join([subject or "", sender or "", " ".join(recipients), body])
    return EmailEntities(
        email_addresses=unique_strings(_EMAIL_RE.findall(text)),
        phone_numbers=unique_strings(_PHONE_RE.findall(text)),
        urls=unique_strings(_URL_RE.findall(text)),
        monetary_amounts=unique_strings(_MONEY_RE.findall(text)),
    )
