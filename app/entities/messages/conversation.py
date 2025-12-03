import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import UUID, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.auth.user import User
from app.entities.base.base import BaseEntity


class Conversation(BaseEntity):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("pam.users.id"))
    title: Mapped[str]
    type: Mapped[str]
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    created_date: Mapped[datetime] = mapped_column(default=func.now())
    updated_date: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    deleted_date: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(User, foreign_keys=[user_id], uselist=False)
