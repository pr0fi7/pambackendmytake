from fastapi import status

from app.core.exceptions.base.exceptions import ExceptionWithStatusAndDetail


class IntegrationNotFoundException(ExceptionWithStatusAndDetail):
    """Raised when an integration is not found."""

    def __init__(self, slug: str):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            f"Integration '{slug}' not found"
        )


class IntegrationNotConnectedException(ExceptionWithStatusAndDetail):
    """Raised when trying to disconnect an integration that is not connected."""

    def __init__(self, slug: str):
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            f"Integration '{slug}' is not connected"
        )


class IntegrationConnectionFailedException(ExceptionWithStatusAndDetail):
    """Raised when an integration connection fails."""

    def __init__(self, message: str):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to connect integration: {message}"
        )


class ComposioAuthConfigNotFoundException(ExceptionWithStatusAndDetail):
    """Raised when no auth config is found for an app in Composio."""

    def __init__(self, slug: str):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            f"No auth config found for app '{slug}'. Please create an auth config first."
        )


class UserEntityNotFoundException(ExceptionWithStatusAndDetail):
    """Raised when a user entity is not found."""

    def __init__(self, user_id: int):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            f"User {user_id} not found or has no Composio entity ID"
        )
