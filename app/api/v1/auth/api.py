from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import AuthDependencies
from app.api.schemas.auth.requests import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.api.schemas.auth.responses import LoginResponse, TokensResponse
from app.models.auth.user import ReadUserModel
from app.services.auth.auth_service import AuthService
from app.services.provisioner.provisioner_service import ProvisionerService
from app.dependencies import (
    get_auth_service,
    get_provisioner_service,
    get_auth_deps,
)

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register_user(
    user_data: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    provisioner_service: Annotated[
        ProvisionerService, Depends(get_provisioner_service)
    ],
) -> ReadUserModel:
    try:
        user = auth_service.register_user(user_data)

        # Provision resources for the new user in the background
        background_tasks.add_task(
            provisioner_service.create_client,
            user_id=user.id,
            backend_port=8000 + (user.id % 1000),  # TODO: improve port assignment logic
        )

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login")
async def auth_user(
    user_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    user = auth_service.verify_login(body=user_data)
    tokens = auth_service.generate_tokens_for_user(user.id)
    return LoginResponse(tokens=tokens, user=user)


@router.post("/logout")
async def logout():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    user = auth_service.get_user_by_email(email=body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid Email address",
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/me")
async def me(
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(get_auth_deps)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ReadUserModel:
    user_id = deps.require_access_token_user_id(token)
    return auth_service.require_user(user_id)


@router.post("/refresh")
async def refresh(
    token: Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer())],
    deps: Annotated[AuthDependencies, Depends(get_auth_deps)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokensResponse:
    user_id = deps.require_refresh_token_user_id(token)
    return auth_service.refresh_tokens_for_user(user_id)
