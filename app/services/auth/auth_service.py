import datetime
import logging
from typing import Optional

import jwt
from fastapi.security import HTTPAuthorizationCredentials
from passlib.apps import custom_app_context as pwd_context

from app.api.schemas.auth.requests import LoginRequest, RegisterRequest
from app.api.schemas.auth.responses import TokensResponse
from app.api.schemas.auth.token_payload import TokenPayload
from app.config import settings
from app.core.enums import TokenTypeEnum
from app.core.exceptions.auth.exceptions import (
    EmailAlreadyRegisteredError,
    FailedAuthorizationException,
    FailedLoginException,
    InvalidAuthorizationSchemeException,
    UserNotFoundByIdOrDeletedException,
)
from app.entities.auth.user import User
from app.models.auth.user import CheckUserPasswordModel, CreateUserModel, ReadUserModel
from app.repositories.auth.auth import AuthRepository


class AuthService:
    """
    Service for authorization purposes.
    """

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    def register_user(self, user_data: RegisterRequest) -> ReadUserModel:
        existing = self._repository.get(email=user_data.email)
        if existing:
            raise EmailAlreadyRegisteredError("Email already registered")

        password_hash = self.set_password(user_data.password)
        create_user_data = CreateUserModel(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            company=user_data.company_name,
            created_date=datetime.datetime.now(),
        )
        return ReadUserModel.model_validate(
            self._repository.create(**create_user_data.model_dump()),
        )

    def set_password(self, password):
        return pwd_context.hash(password)

    def check_password(self, given_password, user_password) -> bool:
        return pwd_context.verify(given_password, user_password)

    @staticmethod
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
                key=settings.AUTH_SECRET_KEY,
                algorithms=["HS256"],
                issuer=settings.TOKEN_ISSUER,
                options={"require": ["iss", "exp", "iat", "sub"]},
            )
            return TokenPayload(**payload_dict)
        except Exception as e:
            logging.info(f"Token verification failed. Error: {e.__repr__()}")
            raise FailedAuthorizationException(e.__repr__())

    def get_user_by_id(self, user_id: int) -> ReadUserModel:
        """Get user by id from the database"""
        return self._repository.get(id=user_id)

    def validate_token(
        self,
        token: HTTPAuthorizationCredentials | None = None,
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
            logging.info(f"Invalid authorization scheme: {token.scheme}")
            raise InvalidAuthorizationSchemeException(token.scheme)

        try:
            payload = self._verify_token(token.credentials)

            # Check if token type is the same as expected
            if payload.token_type != token_type:
                raise FailedAuthorizationException("wrong token type")

            return int(payload.sub)
        except Exception as e:
            if throw_errors:
                raise e
            return None

    def require_user_by_email(self, email: str) -> CheckUserPasswordModel:
        user = self._repository.get(email=email)

        if user is None:
            raise FailedLoginException()

        return CheckUserPasswordModel.model_validate(user)

    def get_user_by_email(self, email: str) -> ReadUserModel:
        user = self._repository.get(email=email)

        if user is None:
            raise FailedLoginException()

        return ReadUserModel.model_validate(user)

    def require_user(self, user_id: int) -> ReadUserModel:
        """
        Require user from id
        :param user_id: User id
        :param db_connector: Connector to the database
        :raise UserNotFoundByIdOrDeletedException: when user was not found or was deleted
        :return: user object
        """
        user = self.get_user_by_id(user_id=user_id)

        if user is None:
            raise UserNotFoundByIdOrDeletedException()

        user_data = self._repository.get(id=user.id)

        return ReadUserModel.model_validate(user_data)

    def verify_login(self, body: LoginRequest) -> ReadUserModel:
        user = self.require_user_by_email(email=body.email)

        if not user.check_password(body.password):
            raise FailedLoginException()

        user_data = self._repository.get(id=user.id)
        return ReadUserModel.model_validate(user_data)

    @staticmethod
    def generate_token(user_id: int, token_type: TokenTypeEnum) -> str:
        token_lifetime = token_type.get_token_lifetime()
        payload = TokenPayload(
            iss=settings.TOKEN_ISSUER,
            exp=datetime.datetime.now(datetime.UTC) + token_lifetime,
            iat=datetime.datetime.now(datetime.UTC),
            sub=str(user_id),
            token_type=token_type,
        )

        return jwt.encode(
            payload.model_dump(),
            settings.AUTH_SECRET_KEY,
            algorithm="HS256",
        )

    def generate_tokens_for_user(self, user_id: int) -> TokensResponse:
        return TokensResponse(
            access_token=self.generate_token(user_id, TokenTypeEnum.ACCESS),
            refresh_token=self.generate_token(user_id, TokenTypeEnum.REFRESH),
        )

    def refresh_tokens_for_user(self, user_id: int) -> TokensResponse:
        return self.generate_tokens_for_user(user_id)

    @staticmethod
    def create_reset_password_token(email: str) -> str:
        data = {
            "sub": email,
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=10),
        }
        token = jwt.encode(
            data,
            settings.AUTH_SECRET_KEY,
            algorithm="HS256",
        )
        return token
