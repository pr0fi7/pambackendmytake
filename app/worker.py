import asyncio

from app.celery_app import celery_app
from app.container import ApplicationContainer
from app.db.database import DatabaseConnector
from app.entities.workflows.workflow import Workflow
from app.models.auth.user import ReadUserModel


@celery_app.task(name="app.worker.execute_workflow")
def execute_workflow(workflow_id: str):
    container = ApplicationContainer()
    container.init_resources()
    workflow_service = container.workflow_service()
    auth_service = container.auth_service()

    asyncio.run(run_workflow(workflow_service, auth_service, workflow_id))


async def run_workflow(
    workflow_service,
    auth_service,
    workflow_id: str,
):
    workflow = None
    with DatabaseConnector() as db:
        workflow = db.session.query(Workflow).filter_by(id=workflow_id).first()
        if not workflow:
            return

    user = ReadUserModel.model_validate(auth_service.get_user_by_id(workflow.user_id))

    await workflow_service.run_workflow(workflow_id, user)
