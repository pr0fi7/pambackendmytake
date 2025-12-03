from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import (
    Configuration,
    DependenciesContainer,
    Container,
)

from app.services.auth.container import AuthContainer


class ServicesContainer(DeclarativeContainer):
    config = Configuration()
    gateway = DependenciesContainer()

    auth = Container(
        AuthContainer,
        config=config,
        gateway=gateway,
    )
