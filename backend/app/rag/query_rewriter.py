import logging
from typing import Any

from app.ai.llm_provider import get_model


logger = logging.getLogger(__name__)


def format_history_for_rewriting(
    messages: list[dict[str, Any]],
) -> str:
    """
    Format recent conversation messages for query rewriting.
    """

    if not messages:
        return "No previous conversation history."

    formatted_messages: list[str] = []

    for message in messages:
        role = str(
            message.get("role", "unknown")
        ).capitalize()

        content = str(
            message.get("content", "")
        ).strip()

        if content:
            formatted_messages.append(
                f"{role}: {content}"
            )

    return "\n".join(formatted_messages)


def rewrite_search_query(
    *,
    question: str,
    conversation_history: list[dict[str, Any]],
    provider: str,
) -> str:
    """
    Rewrite a follow-up question into a standalone search query.
    """

    cleaned_question = question.strip()

    if not conversation_history:
        return cleaned_question

    history_text = format_history_for_rewriting(
        conversation_history
    )

    prompt = f"""
You rewrite user questions for document retrieval.

Use the conversation history only to resolve references such as:
- it
- they
- those
- this
- that
- the previous answer

Return one standalone search query.

Rules:
1. Preserve the user's original meaning.
2. Do not answer the question.
3. Do not add facts not present in the conversation.
4. Keep the rewritten query concise.
5. Return only the rewritten query.
6. Use the same language as the user's question.

Conversation history:

{history_text}

Current question:

{cleaned_question}

Standalone search query:
""".strip()

    try:
        model = get_model(provider)
        response = model.invoke(prompt)

        if hasattr(response, "content"):
            rewritten_query = str(
                response.content
            ).strip()
        else:
            rewritten_query = str(
                response
            ).strip()

    except Exception:
        logger.exception(
            "Query rewriting failed. Using original question."
        )
        return cleaned_question

    if not rewritten_query:
        return cleaned_question

    logger.info(
        "Query rewritten: original=%r rewritten=%r",
        cleaned_question,
        rewritten_query,
    )

    return rewritten_query