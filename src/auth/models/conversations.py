import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey, func, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.models.user import User
from src.common.models.base_model import DeclarativeBase


class Conversation(DeclarativeBase):
    __tablename__ = 'conversations'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str]
    type: Mapped[str]
    created_date: Mapped[datetime] = mapped_column(default=func.now())
    updated_date: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    deleted_date: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(User, foreign_keys=[user_id], uselist=False)
