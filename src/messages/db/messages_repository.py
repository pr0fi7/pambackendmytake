import uuid
from datetime import datetime

from src.auth.models.messages import Message
from src.common.db.database_connector import DatabaseConnector


def get_root_user_messages(
        db_connector: DatabaseConnector,
        user_id: int,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: datetime | None = None,
) -> list[Message]:
    query = (
        db_connector.session.query(Message)
        .filter(Message.user_id == user_id, Message.role == 'user', Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
    )

    if cursor:
        query = query.filter(Message.timestamp < cursor)

    return query.limit(limit).all()


def get_messages_for_parent_message_id(
        db_connector: DatabaseConnector,
        parent_message_ids: list[uuid.UUID],
) -> list[Message]:
    return (
        db_connector.session.query(Message)
        .filter(Message.parent_message_id.in_(parent_message_ids))
        .order_by(Message.timestamp.asc())
        .all()
    )


def get_has_older_messages(
        db_connector: DatabaseConnector,
        user_id: int,
        conversation_id: uuid.UUID,
        cursor: datetime,
) -> bool:
    count = (
        db_connector.session.query(Message)
        .filter(
            Message.user_id == user_id,
            Message.role == 'user',
            Message.conversation_id == conversation_id,
            Message.timestamp < cursor,
        )
        .count()
    )
    return count > 0
