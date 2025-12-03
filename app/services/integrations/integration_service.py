import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from composio import Composio

from app.api.schemas.integrations.responses import (
    ConnectIntegrationResponse,
    DisconnectIntegrationResponse,
    IntegrationCallbackResponse,
    IntegrationItem,
    ListIntegrationsResponse,
)
from app.config import settings
from app.core.exceptions.integrations.exceptions import (
    ComposioAuthConfigNotFoundException,
    IntegrationConnectionFailedException,
    IntegrationNotConnectedException,
    IntegrationNotFoundException,
    UserEntityNotFoundException,
)
from app.repositories.auth.auth import AuthRepository
from app.repositories.integrations.integrations import IntegrationRepository

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing Composio integrations using v2 API."""

    def __init__(
        self,
        integration_repository: IntegrationRepository,
        auth_repository: AuthRepository,
    ):
        self._integration_repository = integration_repository
        self._auth_repository = auth_repository
        self._composio_client: Optional[Composio] = None

    @property
    def composio(self) -> Composio:
        """Lazy-load Composio client."""
        if self._composio_client is None:
            self._composio_client = Composio(api_key=settings.COMPOSIO_API_KEY)
        return self._composio_client

    def get_or_create_entity_id(self, user_id: int) -> str:
        """Get or create Composio entity ID for a user."""
        user = self._auth_repository.get(id=user_id)
        if not user:
            raise UserEntityNotFoundException(user_id)

        if user.composio_entity_id:
            return user.composio_entity_id

        # Create new entity ID based on user email or ID
        entity_id = f"user_{user.email.split('@')[0]}_{user.id}"
        self._auth_repository.update({"composio_entity_id": entity_id}, id=user_id)
        logger.info(f"Created Composio entity ID for user {user_id}: {entity_id}")
        return entity_id

    def list_user_integrations(self, user_id: int) -> ListIntegrationsResponse:
        """
        Get all available integrations and mark which ones are active for the user.
        Returns ListIntegrationsResponse with 'active' and 'inactive' lists.
        """
        # Get all available integrations from database
        all_integrations = self._integration_repository.get_all_integrations()

        # Get user's connected integrations
        user_integrations = self._integration_repository.get_user_integrations(user_id)
        connected_integration_ids = {
            ui.integration_id for ui in user_integrations if ui.status == "connected"
        }

        active = []
        inactive = []

        for integration in all_integrations:
            integration_item = IntegrationItem(
                name=integration.name,
                slug=integration.slug,
                image=integration.image_url,
                is_connected=integration.id in connected_integration_ids,
            )

            if integration_item.is_connected:
                active.append(integration_item)
            else:
                inactive.append(integration_item)

        return ListIntegrationsResponse(active=active, inactive=inactive)

    def initiate_connection(
        self,
        user_id: int,
        app_slug: str,
        redirect_url: Optional[str] = None
    ) -> ConnectIntegrationResponse:
        """
        Initiate OAuth connection for a user to connect an app using Composio v2 API.
        Returns authorization URL for user to complete OAuth flow.
        """
        entity_id = self.get_or_create_entity_id(user_id)
        app_slug = app_slug.lower()

        # Get integration by slug
        integration = self._integration_repository.get_integration_by_slug(app_slug)
        if not integration:
            raise IntegrationNotFoundException(app_slug)

        # Create or update user integration record
        self._integration_repository.create_or_update_user_integration(
            user_id=user_id,
            integration_id=integration.id,
            status="pending"
        )

        try:
            # 1. Get auth_config_id for the app
            logger.info(f"Finding auth config for {app_slug}")
            configs_response = self.composio.auth_configs.list()
            auth_config_id = None

            for config in configs_response.items:
                # In Composio v2, toolkit is always present on auth configs
                if config.toolkit.slug.lower() == app_slug:
                    auth_config_id = config.id
                    logger.info(f"Found auth config: {auth_config_id} for {app_slug}")
                    break

            if not auth_config_id:
                raise ComposioAuthConfigNotFoundException(app_slug)

        except ComposioAuthConfigNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get auth config: {e}")
            raise IntegrationConnectionFailedException(f"Failed to retrieve auth config: {e}") from e

        # 2. Initiate OAuth flow using v2 API
        try:
            logger.info(f"Initiating OAuth for user {user_id}/{app_slug}")

            # Use default callback URL if not provided
            callback = redirect_url or f"{settings.API_URL}/v1/integrations/oauth-callback"

            conn_req = self.composio.connected_accounts.initiate(
                user_id=entity_id,
                auth_config_id=auth_config_id,
                callback_url=callback,
                allow_multiple=True,
            )

            logger.info(f"OAuth initiated successfully for user {user_id}/{app_slug}")
            logger.info(f"Redirect URL: {conn_req.redirect_url}")

        except Exception as e:
            logger.error(f"OAuth initiation failed: {e}")
            raise IntegrationConnectionFailedException(f"Failed to initiate OAuth: {e}") from e

        # 3. Start background task to wait for completion
        task = asyncio.create_task(self._wait_for_oauth(entity_id, app_slug, user_id, integration.id))
        # Add error handler to prevent silent failures
        task.add_done_callback(lambda t: logger.error(f"OAuth polling task failed: {t.exception()}") if t.exception() else None)

        return ConnectIntegrationResponse(
            auth_url=conn_req.redirect_url,
            app_slug=app_slug,
            status="pending",
            message=f"Please authorize {app_slug}"
        )

    def _find_and_update_active_connection(
        self,
        entity_id: str,
        app_slug: str,
        user_id: int,
        integration_id: int
    ) -> bool:
        """
        Check Composio for active connection and update database if found.

        Args:
            entity_id: Composio entity ID
            app_slug: Integration slug (lowercase)
            user_id: User ID
            integration_id: Integration ID

        Returns:
            True if active connection found and updated, False otherwise
        """
        accounts = self.composio.connected_accounts.list(user_ids=[entity_id])

        for acc in accounts.items:
            # In Composio v2, toolkit and status are always present
            if acc.toolkit.slug.lower() == app_slug and acc.status == "ACTIVE":
                # Found active connection, update database
                self._integration_repository.create_or_update_user_integration(
                    user_id=user_id,
                    integration_id=integration_id,
                    status="connected",
                    composio_connection_id=acc.id,
                    connected_at=datetime.now(timezone.utc)
                )
                return True

        return False

    async def _wait_for_oauth(
        self,
        entity_id: str,
        app_slug: str,
        user_id: int,
        integration_id: int,
        max_wait: int = 300
    ):
        """
        Poll Composio for OAuth completion using v2 API.
        Updates database when connection becomes active.
        """
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                if self._find_and_update_active_connection(entity_id, app_slug, user_id, integration_id):
                    logger.info(f"[OK] OAuth completed for user {user_id}/{app_slug}")
                    return

            except Exception as e:
                logger.warning(f"Error checking OAuth status: {e}")

            await asyncio.sleep(5)

        logger.warning(f"OAuth timeout for user {user_id}/{app_slug}")

    def update_connection_from_callback(self, user_id: int, app_slug: str) -> IntegrationCallbackResponse:
        """
        Called when frontend receives OAuth callback and notifies backend.
        Checks Composio for active connection and updates database.
        """
        user = self._auth_repository.get(id=user_id)
        if not user or not user.composio_entity_id:
            raise UserEntityNotFoundException(user_id)

        app_slug = app_slug.lower()

        # Get integration by slug
        integration = self._integration_repository.get_integration_by_slug(app_slug)
        if not integration:
            raise IntegrationNotFoundException(app_slug)

        try:
            # Check for active connection and update if found
            if self._find_and_update_active_connection(user.composio_entity_id, app_slug, user_id, integration.id):
                logger.info(f"Updated connection from callback: user {user_id} -> {app_slug}")
                return IntegrationCallbackResponse(
                    success=True,
                    app_slug=app_slug,
                    status="connected"
                )
            else:
                logger.warning(f"No active connection found for user {user_id} -> {app_slug}")
                return IntegrationCallbackResponse(
                    success=False,
                    app_slug=app_slug,
                    status="pending",
                    message="Connection not yet active"
                )
        except Exception as e:
            logger.error(f"Failed to update connection from callback: user {user_id}:{app_slug} - {e}")
            raise

    def disconnect_app(self, user_id: int, app_slug: str) -> DisconnectIntegrationResponse:
        """Disconnect a user's app connection using v2 API."""
        user = self._auth_repository.get(id=user_id)
        if not user:
            raise UserEntityNotFoundException(user_id)

        app_slug = app_slug.lower()

        # Get integration by slug
        integration = self._integration_repository.get_integration_by_slug(app_slug)
        if not integration:
            raise IntegrationNotFoundException(app_slug)

        # Get user integration
        user_integration = self._integration_repository.get_user_integration(user_id, integration.id)

        if not user_integration or user_integration.status != "connected":
            raise IntegrationNotConnectedException(app_slug)

        # Try to revoke from Composio using v2 API
        revoked_from_composio = False
        if user.composio_entity_id:
            try:
                accounts = self.composio.connected_accounts.list(user_ids=[user.composio_entity_id])

                for acc in accounts.items:
                    # In Composio v2, toolkit is always present
                    if acc.toolkit.slug.lower() == app_slug:
                        self.composio.connected_accounts.delete(id=acc.id)
                        revoked_from_composio = True
                        logger.info(f"Deleted connected account from Composio: {acc.id}")
                        break
            except Exception as e:
                logger.warning(f"Failed to revoke Composio account: {e}")

        # Update local database
        self._integration_repository.create_or_update_user_integration(
            user_id=user_id,
            integration_id=integration.id,
            status="disconnected",
            composio_connection_id=None,
            connected_at=None
        )

        logger.info(f"Disconnected: user {user_id} -> {app_slug}")

        return DisconnectIntegrationResponse(
            success=True,
            app_slug=app_slug,
            status="disconnected",
            note="Disconnected from Composio" if revoked_from_composio else "Disconnected locally"
        )
