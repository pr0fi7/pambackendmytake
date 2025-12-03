import uuid

from app.core.enums import WorkflowRunStatusEnum
from app.db.database import DatabaseConnector
from app.entities.workflows.workflow import Workflow, WorkflowRun
from app.repositories.base.base import BaseSessionRepository


class WorkflowRepository(BaseSessionRepository[Workflow]):
    model = Workflow

    def get_workflow_by_id(
        self,
        workflow_id: uuid.UUID,
    ) -> Workflow | None:
        with DatabaseConnector() as db:
            return (
                db.session.query(Workflow)
                .filter(
                    Workflow.id == workflow_id,
                    Workflow.deleted_date.is_(None),
                )
                .one_or_none()
            )

    def get_workflows_by_user_id(
        self,
        user_id: int,
    ) -> list[Workflow]:
        with DatabaseConnector() as db:
            query = db.session.query(Workflow).filter(
                Workflow.user_id == user_id,
                Workflow.deleted_date.is_(None),
            )

            return query.order_by(Workflow.updated_date.desc()).all()

    def add_workflow_run(self, workflow_id):
        with DatabaseConnector() as db:
            workflow = db.session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                return

            run = WorkflowRun(
                workflow_id=workflow.id,
                user_id=workflow.user_id,
                prompt=workflow.prompt,
                status=WorkflowRunStatusEnum.RUNNING,
            )
            db.session.add(run)
            db.session.commit()
            return run

    def finish_workflow_run(self, run_id, conversation_id):
        with DatabaseConnector() as db:
            run = db.session.query(WorkflowRun).filter_by(id=run_id).first()
            run.status = WorkflowRunStatusEnum.SUCCESS
            run.conversation_id = conversation_id
            db.session.commit()
