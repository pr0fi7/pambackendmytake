from typing import Optional
from app.models.auth.user import ReadUserModel
from fastapi.security import HTTPAuthorizationCredentials
from app.config import settings
from app.core.enums import TokenTypeEnum
from app.core.exceptions.auth.exceptions import (
    FailedAuthorizationException,
    NotAuthenticatedException,
)
from app.services.auth.auth_service import AuthService


class AuthDependencies:
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    def require_access_token_user_id(
        self,
        token: Optional[HTTPAuthorizationCredentials],
    ) -> int:
        """Required access-token validator"""
        user_id = self.auth_service.validate_token(token, TokenTypeEnum.ACCESS)
        if user_id is None:
            raise NotAuthenticatedException()
        return user_id

    def require_refresh_token_user_id(
        self,
        token: Optional[HTTPAuthorizationCredentials],
    ) -> int:
        """Required refresh-token validator"""
        user_id = self.auth_service.validate_token(token, TokenTypeEnum.REFRESH)
        if user_id is None:
            raise NotAuthenticatedException()
        return user_id

    def require_user_for_refresh(self, user_id: int) -> ReadUserModel:
        """Required refresh-token user fetch"""
        return self.auth_service.require_user(user_id=user_id)

    def require_harmix_api_key(self, api_key: Optional[str]):
        if api_key != settings.HARMIX_API_KEY:
            raise FailedAuthorizationException("API key is invalid")
