import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.models.conversations import Conversation
from src.auth.models.user import User
from src.common.models.base_model import DeclarativeBase


class Message(DeclarativeBase):
    __tablename__ = 'messages'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('messages.id'))
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('conversations.id'))
    role: Mapped[str]
    content: Mapped[str]
    content_new: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict
    )
    timestamp: Mapped[datetime] = mapped_column(default=func.now())

    user: Mapped[User] = relationship(User, foreign_keys=[user_id], uselist=False)
    parent_message: Mapped['Message'] = relationship(
        'Message',
        foreign_keys=[parent_message_id],
        uselist=False,
    )
    conversation: Mapped['Conversation'] = relationship(
        'Conversation',
        foreign_keys=[conversation_id],
        uselist=False,
    )
