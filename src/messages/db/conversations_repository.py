import uuid

from src.auth.models.conversations import Conversation
from src.common.db.database_connector import DatabaseConnector


def get_conversation_by_id(db_connector: DatabaseConnector, conversation_id: uuid.UUID, ) -> Conversation | None:
    return (
        db_connector.session.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.deleted_date.is_(None),
        )
        .one_or_none()
    )


def get_conversations_by_user_id(
        db_connector: DatabaseConnector,
        user_id: int,
        conversation_type: str | None = None,
) -> list[Conversation]:
    query = db_connector.session.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.deleted_date.is_(None),
    )

    if conversation_type:
        query = query.filter(Conversation.type == conversation_type)

    return query.order_by(Conversation.updated_date.desc()).all()
