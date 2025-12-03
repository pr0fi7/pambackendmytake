from app.entities.auth.user import User
from app.repositories.base.base import BaseSessionRepository


class AuthRepository(BaseSessionRepository[User]):
    model = User
