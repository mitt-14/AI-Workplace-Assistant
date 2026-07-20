import logging

from fastapi import APIRouter, HTTPException, status

from app.core.conversation_store import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
)
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDeleteResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


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