from fastapi import APIRouter, Depends

from src.auth import service, auth_dependencies
from src.auth.models.user import User
from src.auth.schemas.request_schemas import LoginInput
from src.auth.schemas.response_schemas import LoginResponse, TokensResponse
from src.auth.schemas.user_dto import UserDto
from src.common.db.database_connector import DatabaseConnector
from src.common.dependencies import get_database_connector_dependency
from src.common.utils.handle_and_raise_generic_exception import (
    handle_and_raise_generic_exception,
)

auth_router = APIRouter()


@auth_router.post(
    "/auth/login",
    summary="User login with email and password",
    description="Verify if email and password are correct, return JWT tokens",
    responses={
        401: {"description": "Password is incorrect"},
        403: {"description": "User is not verified"},
        404: {"description": "User with given email could not be found"},
    },
    # dependencies=[Depends(auth_dependencies.require_harmix_api_key_auth)],
)
# @handle_and_raise_generic_exception
def login(
    # body: LoginInput,
    db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
):
    return (
        db_connector.session.query(User)
        .filter(
            User.id == 1,
        )
        .first()
    )
    user = service.verify_login(db_connector=db_connector, body=body)
    tokens = service.generate_tokens_for_user(user.id)

    return LoginResponse(tokens=tokens, user=UserDto.map(user))


@auth_router.post(
    "/auth/refresh",
    summary="Refresh access and refresh tokens",
    description="Provide a valid refresh token in the Authorization header to get a pair of new tokens",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "User is not verified"},
        404: {"description": "User for this token was not found"},
    },
    dependencies=[Depends(auth_dependencies.require_harmix_api_key_auth)],
)
@handle_and_raise_generic_exception
def refresh(
    user: User = Depends(auth_dependencies.require_user_for_refresh_token),
) -> TokensResponse:
    return service.refresh_tokens_for_user(user.id)


@auth_router.get(
    "/auth/me",
    summary="Get current user info",
    description="Get info about the current user",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "User is not verified"},
        404: {"description": "User for this token was not found"},
    },
    dependencies=[Depends(auth_dependencies.require_harmix_api_key_auth)],
)
@handle_and_raise_generic_exception
def get_current_user(user: User = Depends(auth_dependencies.require_user)) -> UserDto:
    return UserDto.map(user)
