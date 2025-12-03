from datetime import datetime
import uuid

from pydantic import BaseModel

from app.entities.messages.conversation import Conversation
from app.models.base.abstract_model import AbstractModel


class ConversationDto(AbstractModel):
    id: uuid.UUID
    user_id: int
    title: str | None
    type: str
    is_pinned: bool | None
    created_date: datetime
    updated_date: datetime | None = None
    deleted_date: datetime | None = None

    @staticmethod
    def map(conversation: Conversation) -> "ConversationDto":
        return ConversationDto(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            type=conversation.type,
            is_pinned=conversation.is_pinned,
            created_date=conversation.created_date,
            deleted_date=conversation.deleted_date,
        )


class CreateConversation(BaseModel):
    user_id: int
    title: str | None
    type: str
    created_date: datetime
