"""
Repository for User table in postgres database.
"""
from typing import Optional, List

from src.auth.models.user import User
from src.common.db.database_connector import DatabaseConnector


def get_user_by_id(db_connector: DatabaseConnector, user_id: int) -> Optional[User]:
    return db_connector.session.query(User).filter(
        User.id == user_id,
    ).first()


def get_user_by_email(db_connector: DatabaseConnector, email: str) -> Optional[User]:
    return db_connector.session.query(User).filter(
        User.email == email,
    ).first()


def get_users_by_email(db_connector: DatabaseConnector, email: str) -> List[User]:
    return db_connector.session.query(User).filter(
        User.email == email,
    ).all()
