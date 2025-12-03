import datetime
import uuid

from app.core.exceptions.workflows.workflows import (
    WorkflowNotFoundError,
)
from app.models.auth.user import ReadUserModel
from app.models.messages.message import CreateMessage, MessageDto
from app.models.workflows.workflow import CreateWorkflow, UpdateWorkflow, WorkflowModel
from app.repositories.workflow.workflow import WorkflowRepository
from app.services.messages.messages_service import MessagesService


class WorkflowService:
    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        message_service: MessagesService,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._message_service = message_service

    async def get_user_workflows(
        self,
        user: ReadUserModel,
    ) -> list[WorkflowModel]:
        workflows = self._workflow_repository.get_workflows_by_user_id(
            user.id,
        )
        return WorkflowModel.validate_list_model(workflows)

    async def get_workflow_details(
        self,
        user: ReadUserModel,
        workflow_id: uuid.UUID,
    ) -> WorkflowModel:
        workflow = WorkflowModel.model_validate(
            self._workflow_repository.get_workflow_by_id(workflow_id)
        )

        if workflow is None or workflow.user_id != user.id:
            raise WorkflowNotFoundError()

        return workflow

    async def create_workflow(
        self,
        data: CreateWorkflow,
        user: ReadUserModel,
    ) -> WorkflowModel:
        data.user_id = user.id
        data.created_date = datetime.datetime.now()
        workflow = self._workflow_repository.create(**data.model_dump())
        return WorkflowModel.model_validate(workflow)

    async def delete_workflow(
        self,
        user: ReadUserModel,
        workflow_id: uuid.UUID,
    ):
        workflow = WorkflowModel.model_validate(
            self._workflow_repository.get_workflow_by_id(workflow_id)
        )

        if workflow is None or workflow.user_id != user.id:
            raise WorkflowNotFoundError()

        workflow.deleted_date = datetime.datetime.now(datetime.timezone.utc)
        self._workflow_repository.update(workflow.model_dump(), id=workflow_id)

    async def patch_workflow(
        self,
        user: ReadUserModel,
        workflow_id: uuid.UUID,
        body: UpdateWorkflow,
    ):
        workflow = WorkflowModel.model_validate(
            self._workflow_repository.get_workflow_by_id(workflow_id)
        )

        if workflow is None or workflow.user_id != user.id:
            raise WorkflowNotFoundError()

        if body.name is not None:
            workflow.name = body.name

        if body.prompt is not None:
            workflow.prompt = body.prompt

        if body.is_active is not None:
            workflow.is_active = body.is_active

        if body.run_options is not None:
            workflow.run_options = body.run_options

        return WorkflowModel.model_validate(
            self._workflow_repository.update(
                workflow.model_dump(),
                id=workflow_id,
            )
        )

    async def run_workflow(self, workflow_id: uuid.UUID, user: ReadUserModel):
        workflow = WorkflowModel.model_validate(
            self._workflow_repository.get_workflow_by_id(workflow_id)
        )

        if workflow is None or workflow.user_id != user.id:
            raise WorkflowNotFoundError()

        run = self._workflow_repository.add_workflow_run(workflow_id)

        conversation = self._message_service.get_or_create_conversation(user, None)
        user_prompt = workflow.prompt.strip()
        user_message = CreateMessage(
            user_id=user.id,
            conversation_id=conversation.id,
            role="user",
            content=user_prompt,
            content_new={"type": "text", "text": user_prompt},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        saved_user_message = (
            MessageDto.model_validate(  # TODO: move repositories calls to service
                self._message_service._message_repository.create(
                    **user_message.model_dump()
                )
            )
        )
        conversation.updated_date = user_message.timestamp
        self._message_service._conversation_repository.update(
            conversation.model_dump(),
            id=conversation.id,
        )

        async for _ in self._message_service.stream_message(
            user,
            user_prompt,
            saved_user_message,
            conversation,
        ):
            pass

        self._workflow_repository.finish_workflow_run(run.id, conversation.id)
