from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.base.base import BaseEntity


class Integration(BaseEntity):
    """Entity for available integrations (e.g., Gmail, Slack, Notion)."""

    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # TODO: Rename database column from 'image' to 'image_url' via migration
    image_url: Mapped[str] = mapped_column("image", String(255))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
