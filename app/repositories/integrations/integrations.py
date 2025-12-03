from datetime import datetime
from typing import List, Optional

from app.db.database import DatabaseConnector
from app.entities.integrations.integration import Integration
from app.entities.integrations.user_integration import UserIntegration
from app.repositories.base.base import BaseSessionRepository


class IntegrationRepository(BaseSessionRepository):
    model = UserIntegration

    def get_all_integrations(self) -> List[Integration]:
        """Get all available integrations."""
        with DatabaseConnector() as db:
            return db.session.query(Integration).all()

    def get_integration_by_slug(self, slug: str) -> Optional[Integration]:
        """Get an integration by its slug."""
        with DatabaseConnector() as db:
            return db.session.query(Integration).filter_by(slug=slug).first()

    def get_user_integrations(self, user_id: int, status: Optional[str] = None) -> List[UserIntegration]:
        """Get all user integrations, optionally filtered by status."""
        with DatabaseConnector() as db:
            query = db.session.query(self.model).filter_by(user_id=user_id)
            if status:
                query = query.filter_by(status=status)
            return query.all()

    def get_user_integration(self, user_id: int, integration_id: int) -> Optional[UserIntegration]:
        """Get a specific user integration."""
        with DatabaseConnector() as db:
            return db.session.query(self.model).filter_by(
                user_id=user_id,
                integration_id=integration_id
            ).first()

    def create_or_update_user_integration(
        self,
        user_id: int,
        integration_id: int,
        status: str,
        composio_connection_id: Optional[str] = None,
        connected_at: Optional[datetime] = None
    ) -> UserIntegration:
        """Create a new user integration or update existing one."""
        with DatabaseConnector() as db:
            existing = db.session.query(self.model).filter_by(
                user_id=user_id,
                integration_id=integration_id
            ).first()

            if existing:
                existing.status = status
                if composio_connection_id is not None:
                    existing.composio_connection_id = composio_connection_id
                if connected_at is not None:
                    existing.connected_at = connected_at
                db.session.commit()
                db.session.refresh(existing)
                return existing
            else:
                new_integration = UserIntegration(
                    user_id=user_id,
                    integration_id=integration_id,
                    status=status,
                    composio_connection_id=composio_connection_id,
                    connected_at=connected_at
                )
                db.session.add(new_integration)
                db.session.commit()
                db.session.refresh(new_integration)
                return new_integration
