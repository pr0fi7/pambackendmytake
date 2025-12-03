"""
Service for authorisation purposes.
"""
import logging
import datetime
from typing import Optional

import jwt
from fastapi.security import HTTPAuthorizationCredentials

from src.auth import constants
from src.auth.db.database import user_repository
from src.auth.exceptions import FailedAuthorizationException, FailedLoginException, UserNotFoundByIdOrDeletedException
from src.auth.exceptions import InvalidAuthorizationSchemeException
from src.auth.models.user import User
from src.auth.schemas.enums.token_type_enum import TokenTypeEnum
from src.auth.schemas.request_schemas import LoginInput
from src.auth.schemas.response_schemas import TokensResponse
from src.auth.schemas.token_payload import TokenPayload
from src.common.db.database_connector import DatabaseConnector


def _verify_token(token: str) -> TokenPayload:
    """
    Verify JWT token
    Uses jwt library to decode the token.
    :param token: Token to verify
    :raise FailedAuthorizationException: in case of error when decoding token. The exception contains the message
    from the original exception from jwt library.
    :return: token payload object
    """
    try:
        payload_dict = jwt.decode(
            jwt=token,
            key=constants.env_config.AUTH_SECRET_KEY,
            algorithms=["HS256"],
            issuer=constants.TOKEN_ISSUER,
            options={'require': ['iss', 'exp', 'iat', 'sub']}
        )
        return TokenPayload(**payload_dict)
    except Exception as e:
        logging.info(f'Token verification failed. Error: {e.__repr__()}')
        raise FailedAuthorizationException(e.__repr__())


def get_user_by_id(db_connector: DatabaseConnector, user_id: int) -> Optional[User]:
    """Get user by id from the database"""
    return user_repository.get_user_by_id(db_connector=db_connector, user_id=user_id)


def validate_token(
        token: HTTPAuthorizationCredentials,
        token_type: TokenTypeEnum = TokenTypeEnum.ACCESS,

        throw_errors: bool = False,
) -> Optional[int]:
    """
    Validate the incoming bearer token
    Validation process:
    1. Check token schema
    2. Parse the payload
    3. Check the token type
    :param token: token from the header
    :param token_type: expected token type
    :param throw_errors: flag whether to throw errors from this function
    :raise InvalidAuthorizationSchemeException: when token has wrong scheme
    :raise FailedAuthorizationException: when token type is not as expected
    :raise other errors which occurs
    :return: user id from the token or None if the token was not validated and errors where ignored
    """
    if token is None:
        return None

    # Check token scheme to be Bearer
    if token.scheme != "Bearer":
        logging.info(f'Invalid authorization scheme: {token.scheme}')
        raise InvalidAuthorizationSchemeException(token.scheme)

    try:
        payload = _verify_token(token.credentials)

        # Check if token type is the same as expected
        if payload.token_type != token_type:
            raise FailedAuthorizationException('wrong token type')

        return int(payload.sub)
    except Exception as e:
        if throw_errors:
            raise e
        return None


def require_user_by_email(db_connector: DatabaseConnector, email: str) -> User:
    user = user_repository.get_user_by_email(db_connector=db_connector, email=email)

    if user is None:
        raise FailedLoginException()

    return user


def require_user(db_connector: DatabaseConnector, user_id: int) -> User:
    """
    Require user from id
    :param user_id: User id
    :param db_connector: Connector to the database
    :raise UserNotFoundByIdOrDeletedException: when user was not found or was deleted
    :return: user object
    """
    user = get_user_by_id(db_connector=db_connector, user_id=user_id)

    if user is None:
        raise UserNotFoundByIdOrDeletedException()

    return user


def verify_login(db_connector: DatabaseConnector, body: LoginInput) -> User:
    user = require_user_by_email(db_connector=db_connector, email=body.email)

    if not user.check_password(body.password):
        raise FailedLoginException()

    return user


def generate_token(user_id: int, token_type: TokenTypeEnum) -> str:
    token_lifetime = token_type.get_token_lifetime()
    payload = TokenPayload(
        iss=constants.TOKEN_ISSUER,
        exp=datetime.datetime.now(datetime.UTC) + token_lifetime,
        iat=datetime.datetime.now(datetime.UTC),
        sub=str(user_id),
        token_type=token_type,
    )

    return jwt.encode(payload.model_dump(), constants.env_config.AUTH_SECRET_KEY, algorithm='HS256')


def generate_tokens_for_user(user_id: int) -> TokensResponse:
    return TokensResponse(
        access_token=generate_token(user_id, TokenTypeEnum.ACCESS),
        refresh_token=generate_token(user_id, TokenTypeEnum.REFRESH)
    )


def refresh_tokens_for_user(user_id: int) -> TokensResponse:
    return generate_tokens_for_user(user_id)
