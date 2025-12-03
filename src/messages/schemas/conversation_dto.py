import uuid

from pydantic import BaseModel

from src.auth.models.conversations import Conversation


class ConversationDto(BaseModel):
    conversation_id: uuid.UUID
    user_id: int
    title: str | None
    type: str
    created_date: str

    @staticmethod
    def map(conversation: Conversation) -> "ConversationDto":
        return ConversationDto(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            type=conversation.type,
            created_date=conversation.created_date.isoformat(),
        )
