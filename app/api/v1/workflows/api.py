import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Depends,
    Response,
    Security,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import AuthDependencies
from app.models.workflows.workflow import (
    CreateWorkflow,
    IntegrationModel,
    UpdateWorkflow,
    WorkflowModel,
    WorkflowSample,
)
from app.services.auth.auth_service import AuthService
from app.services.workflows.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows")


@router.get("")
@inject
async def get_user_workflows(
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> list[WorkflowModel]:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await workflow_service.get_user_workflows(user)


@router.post("")
@inject
async def create_workflow(
    data: CreateWorkflow,
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> WorkflowModel:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await workflow_service.create_workflow(data, user)


@router.get("/workflow/{workflow_id}")
@inject
async def get_workflow_detail(
    workflow_id: uuid.UUID,
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> WorkflowModel:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await workflow_service.get_workflow_details(user, workflow_id)


@router.delete("/workflow/{workflow_id}")
@inject
async def delete_workflow(
    workflow_id: uuid.UUID,
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> Response:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    await workflow_service.delete_workflow(user, workflow_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/workflow/{workflow_id}")
@inject
async def patch_workflow(
    workflow_id: uuid.UUID,
    body: UpdateWorkflow,
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> WorkflowModel:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await workflow_service.patch_workflow(user, workflow_id, body)


@router.post("/workflow/{workflow_id}/run")
@inject
async def run_workflow(
    workflow_id: uuid.UUID,
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    workflow_service: Annotated[WorkflowService, Depends(Provide["workflow_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
) -> Response:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    await workflow_service.run_workflow(workflow_id, user)
    return Response(status_code=status.HTTP_200_OK)


@router.get("/samples")
async def workflow_samples_mock() -> list[WorkflowSample]:
    return [
        WorkflowSample(
            id=uuid.uuid4(),
            name="Missed opportunities identification",
            description="Identify leads that showed interest but did not receive timely follow-ups...",
            prompt="Analyze recent CRM interactions...",
            integrations=[IntegrationModel(name="Gmail", slug="google_gmail")],
        ),
        WorkflowSample(
            id=uuid.uuid4(),
            name="Sales rep dashboard (response time, num of follow ups)",
            description="Generate a performance dashboard...",
            prompt="Create a sales rep performance dashboard...",
            integrations=[
                IntegrationModel(name="Gmail", slug="google_gmail"),
                IntegrationModel(name="Google Calendar", slug="google_calendar"),
            ],
        ),
        WorkflowSample(
            id=uuid.uuid4(),
            name="Relevant Twitter posts searching and comments drafting",
            description="Search for recent Twitter posts...",
            prompt="Find trending Twitter posts...",
            integrations=[IntegrationModel(name="Slack", slug="slack")],
        ),
    ]

