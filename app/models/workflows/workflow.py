import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.core.enums import Meridiem, RepeatEvery, RepeatType, RunVariant
from app.models.base.abstract_model import AbstractModel


class RunOptions(AbstractModel):
    run_variant: RunVariant = Field(...)

    repeat_type: RepeatType | None = Field(default=None)
    repeat_every: RepeatEvery | None = Field(default=None)
    repeat_once_date: str | None = Field(default=None)

    month_day: int | None = Field(default=None, ge=1, le=28)
    week_day: int | None = Field(default=None, ge=1, le=7)
    hour: int | None = Field(default=None, ge=1, le=12)

    meridiem: Meridiem | None = Field(default=None)
    minute: int | None = Field(default=None, ge=0, le=59)


class WorkflowModel(AbstractModel):
    id: uuid.UUID
    user_id: int
    name: str
    prompt: str
    is_active: bool
    run_options: Optional[RunOptions] = None
    created_date: datetime
    updated_date: datetime | None
    deleted_date: datetime | None


class IntegrationModel(AbstractModel):
    name: str
    slug: str


class WorkflowSample(AbstractModel):
    id: uuid.UUID
    name: str
    prompt: str
    description: str
    integrations: List[IntegrationModel] | None


class CreateWorkflow(AbstractModel):
    name: str
    prompt: str
    is_active: bool
    run_options: Optional[RunOptions] = None

    user_id: int | None = None
    created_date: datetime | None = None


class UpdateWorkflow(AbstractModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    is_active: Optional[bool] = None
    run_options: Optional[RunOptions] = None
