import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.messages.message import MessageDto


class TurnSchema(BaseModel):
    turn_id: str
    user_message: MessageDto
    assistant_messages: list[MessageDto]


class GetMessagesResponseSchema(BaseModel):
    conversation_id: uuid.UUID
    conversation_type: str
    turns: list[TurnSchema]
    next_cursor: datetime | None
