import uuid
from datetime import datetime

from pydantic import BaseModel

from src.auth.models.messages import Message


class MessageDto(BaseModel):
    id: uuid.UUID
    user_id: int

    parent_message_id: uuid.UUID | None
    role: str
    content: dict
    timestamp: datetime

    @staticmethod
    def map(message: Message) -> "MessageDto":
        return MessageDto(
            id=message.id,
            user_id=message.user_id,
            parent_message_id=message.parent_message_id,
            role=message.role,
            content=message.content_new,
            timestamp=message.timestamp,
        )
