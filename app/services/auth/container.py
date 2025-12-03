from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, DependenciesContainer, Factory

from app.repositories.auth.auth import AuthRepository
from app.services.auth.auth_service import AuthService


class AuthContainer(DeclarativeContainer):
    """Container for comment-related services."""

    config = Configuration()
    gateway = DependenciesContainer()

    auth_repository = Factory(
        AuthRepository,
        async_session_factory=gateway.async_session.provided.session,
    )

    auth_service = Factory(
        AuthService,
        repository=auth_repository,
    )
