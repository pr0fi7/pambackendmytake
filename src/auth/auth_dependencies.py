"""
Dependencies to use for authorisation of clients, Harmix client and users within Harmix client.
"""
from typing import Optional

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader

from src.auth.exceptions import FailedAuthorizationException
from src.auth.models.user import User
from src.auth.schemas.enums.token_type_enum import TokenTypeEnum
from src.common.db.database_connector import DatabaseConnector
from src.common.dependencies import get_database_connector_dependency
from src.common.utils.handle_and_raise_generic_exception import handle_and_raise_generic_exception
from src.auth import constants, service
from src.auth.exceptions import NotAuthenticatedException

# Object for bearer authorisation
bearer_security = HTTPBearer(auto_error=False)

# Object for api key authorisation
api_key_header = APIKeyHeader(name=constants.API_KEY_NAME, auto_error=False)


@handle_and_raise_generic_exception
def _get_access_token_auth(token: HTTPAuthorizationCredentials = Depends(bearer_security)) -> Optional[int]:
    """
    Optional access token authorisation
    Validates the authorisation token to be an access token.
    :param token: Bearer token in header
    :return: user id from the token or None
    """
    return service.validate_token(token, TokenTypeEnum.ACCESS, False)


@handle_and_raise_generic_exception
def _require_access_token_auth(token: HTTPAuthorizationCredentials = Depends(bearer_security)) -> int:
    """
    Required access token authorisation
    Validates the authorisation token to be an access token.
    :param token: bearer token in header
    :raise NotAuthenticatedException: when user was not authorised
    :return: user id from the token
    """
    user_id = service.validate_token(token, TokenTypeEnum.ACCESS, True)

    if user_id is None:
        raise NotAuthenticatedException()

    return user_id


@handle_and_raise_generic_exception
def _require_refresh_token_auth(token: HTTPAuthorizationCredentials = Depends(bearer_security)) -> int:
    """
    Required refresh token authorisation
    Validates the authorisation token to be a refresh token.
    :param token: bearer token in header
    :raise NotAuthenticatedException: when user was not authorised
    :return: user id from the token
    """
    user_id = service.validate_token(token, TokenTypeEnum.REFRESH, True)

    if user_id is None:
        raise NotAuthenticatedException()

    return user_id


@handle_and_raise_generic_exception
def get_user(
        user_id: Optional[int] = Depends(_get_access_token_auth),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
) -> Optional[User]:
    """
    Optional user authorisation
    :param user_id: user id form the token
    :param db_connector: Connector to the database
    :return: User object if found or None
    """
    if user_id is None:
        return None

    user = service.get_user_by_id(db_connector=db_connector, user_id=user_id)
    return user


@handle_and_raise_generic_exception
def require_user(
        user_id: int = Depends(_require_access_token_auth),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
) -> User:
    """
    Required user authorisation
    :param user_id: user id from the token
    :param db_connector: Connector to the database
    :return: User object
    """
    return service.require_user(db_connector=db_connector, user_id=user_id)


@handle_and_raise_generic_exception
def require_user_for_refresh_token(
        user_id: int = Depends(_require_refresh_token_auth),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
) -> User:
    """
    Required user authorisation with refresh token
    :param user_id: user id from the token
    :param db_connector: Connector to the database
    :return: User object
    """
    return service.require_user(db_connector=db_connector, user_id=user_id)


@handle_and_raise_generic_exception
def require_harmix_api_key_auth(api_key: str = Security(api_key_header)):
    """
    Required Harmix client authorisation with API key
    Compares the API key with the Harmix key and throw an error in case of mismatch.
    :param api_key: API key from the header
    :raises FailedAuthorizationException: when API key is wrong
    """
    if api_key != constants.env_config.HARMIX_API_KEY:
        raise FailedAuthorizationException('API key is invalid')
