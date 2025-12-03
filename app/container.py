from dependency_injector import containers, providers

from app.api.dependencies.auth import AuthDependencies
from app.config import settings

# from app.gateways.container import GatewayContainer
from app.repositories.auth.auth import AuthRepository
from app.repositories.messages.conversation import ConversationRepository
from app.repositories.messages.messages import MessageRepository
from app.repositories.workflow.workflow import WorkflowRepository
from app.repositories.integrations.integrations import IntegrationRepository
from app.services.auth.auth_service import AuthService
from app.services.messages.messages_service import MessagesService
from app.services.provisioner.provisioner_service import ProvisionerService
from app.services.workflows.workflow_service import WorkflowService
from app.services.integrations.integration_service import IntegrationService
from app.services.mcp.mcp_service import MCPService


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[settings])

    wiring_config = containers.WiringConfiguration(
        packages=[
            "app.api.v1.auth",
            "app.api.v1.messages",
            "app.api.v1.workflows",
            "app.api.v1.integrations",
            "app.api.v1.mcp",
        ]
    )

    auth_repository = providers.Factory(AuthRepository)
    message_repository = providers.Factory(MessageRepository)
    workflow_repository = providers.Factory(WorkflowRepository)
    conversation_repository = providers.Factory(ConversationRepository)
    integration_repository = providers.Factory(IntegrationRepository)

    auth_service = providers.Factory(
        AuthService,
        repository=auth_repository,
    )

    message_service = providers.Factory(
        MessagesService,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
    )

    provisioner_service = providers.Factory(
        ProvisionerService,
        auth_repository=auth_repository,
    )

    workflow_service = providers.Factory(
        WorkflowService,
        workflow_repository=workflow_repository,
        message_service=message_service,
    )

    integration_service = providers.Factory(
        IntegrationService,
        integration_repository=integration_repository,
        auth_repository=auth_repository,
    )

    mcp_service = providers.Factory(MCPService)

    auth_deps = providers.Factory(AuthDependencies, auth_service=auth_service)
