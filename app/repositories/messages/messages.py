import uuid
from datetime import datetime

from app.db.database import DatabaseConnector
from app.entities.messages.message import Message
from app.repositories.base.base import BaseSessionRepository


class MessageRepository(BaseSessionRepository[Message]):
    model = Message

    def get_root_user_messages(
        self,
        user_id: int,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: datetime | None = None,
    ) -> list[Message]:
        with DatabaseConnector() as db:
            query = (
                db.session.query(Message)
                .filter(
                    Message.user_id == user_id,
                    Message.role == "user",
                    Message.conversation_id == conversation_id,
                )
                .order_by(Message.timestamp.desc())
            )

            if cursor:
                query = query.filter(Message.timestamp < cursor)

            return query.limit(limit).all()

    def get_messages_for_parent_message_id(
        self,
        parent_message_ids: list[uuid.UUID],
    ) -> list[Message]:
        with DatabaseConnector() as db:
            return (
                db.session.query(Message)
                .filter(Message.parent_message_id.in_(parent_message_ids))
                .order_by(Message.timestamp.asc())
                .all()
            )

    def get_has_older_messages(
        self,
        user_id: int,
        conversation_id: uuid.UUID,
        cursor: datetime,
    ) -> bool:
        with DatabaseConnector() as db:
            count = (
                db.session.query(Message)
                .filter(
                    Message.user_id == user_id,
                    Message.role == "user",
                    Message.conversation_id == conversation_id,
                    Message.timestamp < cursor,
                )
                .count()
            )
            return count > 0
