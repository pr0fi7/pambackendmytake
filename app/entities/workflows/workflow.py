import uuid
from datetime import datetime

from app.core.enums import WorkflowRunStatusEnum
import sqlalchemy as sa
from sqlalchemy import UUID, Boolean, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.entities.auth.user import User
from app.entities.base.base import BaseEntity


class Workflow(BaseEntity):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("pam.users.id"))
    name: Mapped[str]
    prompt: Mapped[str]
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    run_options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_date: Mapped[datetime] = mapped_column(default=func.now())
    updated_date: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    deleted_date: Mapped[datetime | None] = mapped_column(nullable=True)

    schedule: Mapped["WorkflowSchedule"] = relationship(
        "WorkflowSchedule", back_populates="workflow", uselist=False
    )
    user: Mapped[User] = relationship(User, foreign_keys=[user_id], uselist=False)


class WorkflowSchedule(BaseEntity):
    __tablename__ = "workflow_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pam.workflows.id"), nullable=False
    )

    repeat_every: Mapped[str]  # "hour", "day", "week"
    week_day: Mapped[int | None]  # 1–7
    hour: Mapped[int | None]
    minute: Mapped[int | None]
    meridiem: Mapped[str | None]  # "AM" / "PM"

    created_date: Mapped[datetime] = mapped_column(default=func.now())
    updated_date: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    workflow: Mapped["Workflow"] = relationship(back_populates="schedule")


class WorkflowRun(BaseEntity):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("pam.users.id"), nullable=False)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pam.workflows.id"), nullable=False
    )
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String,
        default=WorkflowRunStatusEnum.PENDING,
    )
    created_date: Mapped[datetime] = mapped_column(default=func.now())
    updated_date: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(User, backref="workflow_runs")
    workflow: Mapped[Workflow] = relationship(Workflow, backref="workflow_runs")
