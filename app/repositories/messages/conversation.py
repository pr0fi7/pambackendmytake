import uuid

from app.db.database import DatabaseConnector
from app.entities.messages.conversation import Conversation
from app.repositories.base.base import BaseSessionRepository


class ConversationRepository(BaseSessionRepository[Conversation]):
    model = Conversation

    def get_conversation_by_id(
        self,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        with DatabaseConnector() as db:
            return (
                db.session.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.deleted_date.is_(None),
                )
                .one_or_none()
            )

    def get_conversations_by_user_id(
        self,
        user_id: int,
        conversation_type: str | None = None,
    ) -> list[Conversation]:
        with DatabaseConnector() as db:
            query = db.session.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.deleted_date.is_(None),
            )

            if conversation_type:
                query = query.filter(Conversation.type == conversation_type)

            return query.order_by(Conversation.updated_date.desc()).all()
