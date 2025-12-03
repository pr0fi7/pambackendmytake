from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base.base import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(default=func.now())
    email: Mapped[str]
    password_hash: Mapped[str | None]

    name: Mapped[str]
    company: Mapped[str | None]

    server_host: Mapped[str | None]
    composio_entity_id: Mapped[str | None]

