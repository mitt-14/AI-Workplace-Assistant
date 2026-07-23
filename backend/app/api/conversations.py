import logging
import re
from datetime import datetime
from typing import Any
from io import BytesIO

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from xml.sax.saxutils import escape

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import Response

from app.core.conversation_store import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    rename_conversation,
    search_conversations,
)
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDeleteResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationRenameRequest,
    ConversationRenameResponse,
    ConversationResponse,
    ConversationSearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

def create_safe_filename(title: str) -> str:
    """
    Convert a conversation title into a safe filename.
    """

    cleaned_title = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        title.strip(),
    )

    cleaned_title = cleaned_title.strip("-_")

    if not cleaned_title:
        return "conversation"

    return cleaned_title[:100]


def format_export_datetime(value: Any) -> str:
    """
    Format SQLite or datetime values for conversation exports.
    """

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def build_conversation_markdown(
    *,
    conversation: dict[str, Any],
    messages: list[dict[str, Any]],
) -> str:
    """
    Convert a conversation and its messages into Markdown.
    """

    lines: list[str] = [
        f"# {conversation['title']}",
        "",
        f"- Conversation ID: `{conversation['conversation_id']}`",
        (
            "- Created: "
            f"{format_export_datetime(conversation['created_at'])}"
        ),
        (
            "- Updated: "
            f"{format_export_datetime(conversation['updated_at'])}"
        ),
        f"- Message count: {conversation['message_count']}",
        "",
        "---",
        "",
    ]

    if not messages:
        lines.extend(
            [
                "_This conversation has no messages._",
                "",
            ]
        )

        return "\n".join(lines)

    for index, message in enumerate(
        messages,
        start=1,
    ):
        role = str(
            message.get("role", "unknown")
        ).strip().lower()

        heading = (
            "User"
            if role == "user"
            else "Assistant"
        )

        lines.extend(
            [
                f"## {index}. {heading}",
                "",
            ]
        )

        provider = message.get("provider")

        if provider:
            lines.extend(
                [
                    f"**Provider:** {provider}",
                    "",
                ]
            )

        created_at = message.get("created_at")

        if created_at:
            lines.extend(
                [
                    (
                        "**Created:** "
                        f"{format_export_datetime(created_at)}"
                    ),
                    "",
                ]
            )

        content = str(
            message.get("content", "")
        ).strip()

        lines.extend(
            [
                content or "_Empty message_",
                "",
            ]
        )

        sources = message.get("sources", [])

        if sources:
            lines.extend(
                [
                    "### Sources",
                    "",
                ]
            )

            for source_index, source in enumerate(
                sources,
                start=1,
            ):
                filename = str(
                    source.get(
                        "filename",
                        "Unknown document",
                    )
                )

                page_number = source.get(
                    "page_number"
                )

                chunk_index = source.get(
                    "chunk_index"
                )

                relevance_score = source.get(
                    "relevance_score"
                )

                source_line = (
                    f"{source_index}. **{filename}**"
                )

                if page_number is not None:
                    source_line += (
                        f" — page {page_number}"
                    )

                if chunk_index is not None:
                    source_line += (
                        f" — chunk {chunk_index}"
                    )

                if relevance_score is not None:
                    source_line += (
                        " — relevance "
                        f"{float(relevance_score):.4f}"
                    )

                lines.append(source_line)

                text_preview = str(
                    source.get(
                        "text_preview",
                        "",
                    )
                ).strip()

                if text_preview:
                    lines.extend(
                        [
                            "",
                            f"   > {text_preview}",
                        ]
                    )

                lines.append("")

        lines.extend(
            [
                "---",
                "",
            ]
        )

    return "\n".join(lines)

def format_pdf_text(value: Any) -> str:
    """
    Escape text so it can safely be used inside a ReportLab Paragraph.
    """

    text = str(value or "").strip()

    if not text:
        return ""

    escaped_text = escape(text)

    return escaped_text.replace(
        "\n",
        "<br/>",
    )


def add_pdf_page_number(
    canvas: Any,
    document: Any,
) -> None:
    """
    Add a page number to each exported PDF page.
    """

    canvas.saveState()

    page_number = canvas.getPageNumber()

    canvas.setFont(
        "Helvetica",
        9,
    )

    canvas.drawCentredString(
        A4[0] / 2,
        12 * mm,
        f"Page {page_number}",
    )

    canvas.restoreState()


def build_conversation_pdf(
    *,
    conversation: dict[str, Any],
    messages: list[dict[str, Any]],
) -> bytes:
    """
    Convert a conversation and its messages into PDF bytes.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=22 * mm,
        title=str(
            conversation["title"]
        ),
        author="AI Workplace Assistant",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="ConversationTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=25,
        spaceAfter=14,
    )

    metadata_style = ParagraphStyle(
        name="ConversationMetadata",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceAfter=4,
    )

    message_heading_style = ParagraphStyle(
        name="MessageHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    message_text_style = ParagraphStyle(
        name="MessageText",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=10,
    )

    source_heading_style = ParagraphStyle(
        name="SourceHeading",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=6,
    )

    source_style = ParagraphStyle(
        name="SourceText",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        leftIndent=8 * mm,
        spaceAfter=6,
    )

    story: list[Any] = []

    story.append(
        Paragraph(
            format_pdf_text(
                conversation["title"]
            ),
            title_style,
        )
    )

    story.append(
        Paragraph(
            (
                "<b>Conversation ID:</b> "
                f"{format_pdf_text(conversation['conversation_id'])}"
            ),
            metadata_style,
        )
    )

    story.append(
        Paragraph(
            (
                "<b>Created:</b> "
                f"{format_pdf_text(format_export_datetime(conversation['created_at']))}"
            ),
            metadata_style,
        )
    )

    story.append(
        Paragraph(
            (
                "<b>Updated:</b> "
                f"{format_pdf_text(format_export_datetime(conversation['updated_at']))}"
            ),
            metadata_style,
        )
    )

    story.append(
        Paragraph(
            (
                "<b>Message count:</b> "
                f"{conversation['message_count']}"
            ),
            metadata_style,
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    if not messages:
        story.append(
            Paragraph(
                "<i>This conversation has no messages.</i>",
                message_text_style,
            )
        )

    for index, message in enumerate(
        messages,
        start=1,
    ):
        role = str(
            message.get("role", "unknown")
        ).strip().lower()

        heading = (
            "User"
            if role == "user"
            else "Assistant"
        )

        story.append(
            Paragraph(
                f"{index}. {heading}",
                message_heading_style,
            )
        )

        provider = message.get("provider")

        if provider:
            story.append(
                Paragraph(
                    (
                        "<b>Provider:</b> "
                        f"{format_pdf_text(provider)}"
                    ),
                    metadata_style,
                )
            )

        created_at = message.get("created_at")

        if created_at:
            story.append(
                Paragraph(
                    (
                        "<b>Created:</b> "
                        f"{format_pdf_text(format_export_datetime(created_at))}"
                    ),
                    metadata_style,
                )
            )

        content = format_pdf_text(
            message.get("content", "")
        )

        story.append(
            Paragraph(
                content or "<i>Empty message</i>",
                message_text_style,
            )
        )

        sources = message.get(
            "sources",
            [],
        )

        if sources:
            story.append(
                Paragraph(
                    "Sources",
                    source_heading_style,
                )
            )

            for source_index, source in enumerate(
                sources,
                start=1,
            ):
                filename = format_pdf_text(
                    source.get(
                        "filename",
                        "Unknown document",
                    )
                )

                source_parts = [
                    f"<b>{source_index}. {filename}</b>"
                ]

                page_number = source.get(
                    "page_number"
                )

                if page_number is not None:
                    source_parts.append(
                        f"page {page_number}"
                    )

                chunk_index = source.get(
                    "chunk_index"
                )

                if chunk_index is not None:
                    source_parts.append(
                        f"chunk {chunk_index}"
                    )

                relevance_score = source.get(
                    "relevance_score"
                )

                if relevance_score is not None:
                    source_parts.append(
                        (
                            "relevance "
                            f"{float(relevance_score):.4f}"
                        )
                    )

                source_description = " - ".join(
                    source_parts
                )

                text_preview = format_pdf_text(
                    source.get(
                        "text_preview",
                        "",
                    )
                )

                if text_preview:
                    source_description += (
                        f"<br/><i>{text_preview}</i>"
                    )

                story.append(
                    Paragraph(
                        source_description,
                        source_style,
                    )
                )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

    document.build(
        story,
        onFirstPage=add_pdf_page_number,
        onLaterPages=add_pdf_page_number,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
)
async def create_new_conversation(
    request: ConversationCreateRequest,
) -> ConversationResponse:
    conversation = create_conversation(
        title=request.title,
    )

    return ConversationResponse(
        **conversation
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List conversations",
)
async def get_conversations() -> ConversationListResponse:
    conversations = list_conversations()

    return ConversationListResponse(
        conversation_count=len(conversations),
        conversations=[
            ConversationResponse(**conversation)
            for conversation in conversations
        ],
        status="completed",
    )

@router.get(
    "/search",
    response_model=ConversationSearchResponse,
    summary="Search conversations",
)
async def search_existing_conversations(
    q: str = Query(
        min_length=1,
        max_length=200,
        description=(
            "Text to search for in conversation "
            "titles and messages."
        ),
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of results to skip.",
    ),
) -> ConversationSearchResponse:
    cleaned_query = q.strip()

    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query cannot be empty.",
        )

    conversations, total_count = (
        search_conversations(
            query=cleaned_query,
            limit=limit,
            offset=offset,
        )
    )

    logger.info(
        "Conversation search API completed: "
        "query=%s result_count=%s total_count=%s",
        cleaned_query,
        len(conversations),
        total_count,
    )

    return ConversationSearchResponse(
        query=cleaned_query,
        result_count=len(conversations),
        total_count=total_count,
        limit=limit,
        offset=offset,
        conversations=[
            ConversationResponse(**conversation)
            for conversation in conversations
        ],
        status="completed",
    )

@router.get(
    "/{conversation_id}/export/markdown",
    summary="Export a conversation as Markdown",
    response_class=Response,
)
async def export_conversation_markdown(
    conversation_id: str,
) -> Response:
    """
    Download a conversation as a Markdown file.
    """

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = get_messages(
        conversation_id
    )

    markdown_content = build_conversation_markdown(
        conversation=conversation,
        messages=messages,
    )

    filename = create_safe_filename(
        conversation["title"]
    )

    logger.info(
        "Conversation exported as Markdown: "
        "conversation_id=%s message_count=%s",
        conversation_id,
        len(messages),
    )

    return Response(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}.md"'
            ),
        },
    )

@router.get(
    "/{conversation_id}/export/pdf",
    summary="Export a conversation as PDF",
    response_class=Response,
)
async def export_conversation_pdf(
    conversation_id: str,
) -> Response:
    """
    Download a conversation as a PDF file.
    """

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = get_messages(
        conversation_id
    )

    try:
        pdf_content = build_conversation_pdf(
            conversation=conversation,
            messages=messages,
        )

    except Exception:
        logger.exception(
            "Conversation PDF export failed: "
            "conversation_id=%s",
            conversation_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate conversation PDF.",
        )

    filename = create_safe_filename(
        conversation["title"]
    )

    logger.info(
        "Conversation exported as PDF: "
        "conversation_id=%s message_count=%s",
        conversation_id,
        len(messages),
    )

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}.pdf"'
            ),
        },
    )

@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation history",
)
async def get_conversation_history(
    conversation_id: str,
) -> ConversationDetailResponse:
    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = get_messages(
        conversation_id
    )

    return ConversationDetailResponse(
        **conversation,
        messages=[
            ConversationMessageResponse(
                message_id=message["message_id"],
                conversation_id=message[
                    "conversation_id"
                ],
                role=message["role"],
                content=message["content"],
                provider=message["provider"],
                created_at=message["created_at"],
            )
            for message in messages
        ],
        status="completed",
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationRenameResponse,
    summary="Rename a conversation",
)
async def rename_existing_conversation(
    conversation_id: str,
    request: ConversationRenameRequest,
) -> ConversationRenameResponse:
    conversation = rename_conversation(
        conversation_id,
        request.title,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    logger.info(
        "Conversation renamed: conversation_id=%s",
        conversation_id,
    )

    return ConversationRenameResponse(
        **conversation,
        status="completed",
    )


@router.delete(
    "/{conversation_id}",
    response_model=ConversationDeleteResponse,
    summary="Delete a conversation",
)
async def remove_conversation(
    conversation_id: str,
) -> ConversationDeleteResponse:
    deleted = delete_conversation(
        conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    logger.info(
        "Conversation deleted: conversation_id=%s",
        conversation_id,
    )

    return ConversationDeleteResponse(
        conversation_id=conversation_id,
        status="deleted",
    )
