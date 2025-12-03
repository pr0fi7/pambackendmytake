from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import AuthDependencies
from app.api.schemas.integrations.requests import (
    ConnectIntegrationRequest,
    DisconnectIntegrationRequest,
    IntegrationCallbackRequest,
)
from app.api.schemas.integrations.responses import (
    ConnectIntegrationResponse,
    DisconnectIntegrationResponse,
    IntegrationCallbackResponse,
    ListIntegrationsResponse,
)
from app.container import ApplicationContainer
from app.services.integrations.integration_service import IntegrationService

router = APIRouter(prefix="/integrations")
bearer = HTTPBearer(auto_error=False)


# ----------------------------------------
# GET /integrations
# ----------------------------------------
@router.get("/", response_model=ListIntegrationsResponse)
@inject
async def list_integrations(
    integration_service: IntegrationService = Depends(Provide[ApplicationContainer.integration_service]),
    auth_deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    token: HTTPAuthorizationCredentials = Depends(bearer),
):
    """
    Get all available integrations and mark which ones are active for the current user.
    """
    user_id = auth_deps.require_access_token_user_id(token)
    result = integration_service.list_user_integrations(user_id)
    return result


# ----------------------------------------
# POST /integrations/connect
# ----------------------------------------
@router.post("/connect", response_model=ConnectIntegrationResponse)
@inject
async def connect_integration(
    payload: ConnectIntegrationRequest,
    integration_service: IntegrationService = Depends(Provide[ApplicationContainer.integration_service]),
    auth_deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    token: HTTPAuthorizationCredentials = Depends(bearer),
):
    """
    Initiate OAuth connection for an integration.
    Returns an OAuth URL for the user to authorize.
    """
    user_id = auth_deps.require_access_token_user_id(token)
    return integration_service.initiate_connection(
        user_id=user_id,
        app_slug=payload.slug,
        redirect_url=payload.redirect_url
    )


# ----------------------------------------
# POST /integrations/oauth-callback
# ----------------------------------------
@router.post("/oauth-callback", response_model=IntegrationCallbackResponse)
@inject
async def oauth_callback(
    payload: IntegrationCallbackRequest,
    integration_service: IntegrationService = Depends(Provide[ApplicationContainer.integration_service]),
    auth_deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    token: HTTPAuthorizationCredentials = Depends(bearer),
):
    """
    Called by frontend after OAuth redirect from Composio.
    Updates the connection status in the database.
    """
    user_id = auth_deps.require_access_token_user_id(token)
    return integration_service.update_connection_from_callback(
        user_id=user_id,
        app_slug=payload.slug
    )


# ----------------------------------------
# POST /integrations/disconnect
# ----------------------------------------
@router.post("/disconnect", response_model=DisconnectIntegrationResponse)
@inject
async def disconnect_integration(
    payload: DisconnectIntegrationRequest,
    integration_service: IntegrationService = Depends(Provide[ApplicationContainer.integration_service]),
    auth_deps: AuthDependencies = Depends(Provide[ApplicationContainer.auth_deps]),
    token: HTTPAuthorizationCredentials = Depends(bearer),
):
    """
    Disconnect a user's integration.
    This revokes the OAuth connection in Composio and updates local database.
    """
    user_id = auth_deps.require_access_token_user_id(token)
    return integration_service.disconnect_app(
        user_id=user_id,
        app_slug=payload.slug
    )
