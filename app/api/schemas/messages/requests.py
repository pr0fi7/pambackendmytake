import uuid

from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    prompt: str
    conversation_id: uuid.UUID | None = None


class PatchConversationRequest(BaseModel):
    title: str | None = None
    type: str | None = None
    is_pinned: bool | None = None
