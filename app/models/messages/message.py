import uuid
from datetime import datetime

from pydantic import BaseModel

from app.entities.messages.message import Message
from app.models.base.abstract_model import AbstractModel


class MessageDto(AbstractModel):
    id: uuid.UUID
    user_id: int

    parent_message_id: uuid.UUID | None
    role: str
    content: dict | str
    content_new: dict
    timestamp: datetime

    @staticmethod
    def map(message: Message) -> "MessageDto":
        return MessageDto(
            id=message.id,
            user_id=message.user_id,
            parent_message_id=message.parent_message_id,
            role=message.role,
            content=message.content_new,
            content_new=message.content_new,
            timestamp=message.timestamp,
        )


class CreateMessage(BaseModel):
    user_id: int

    parent_message_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    role: str
    content: dict | str
    content_new: dict
    timestamp: datetime
