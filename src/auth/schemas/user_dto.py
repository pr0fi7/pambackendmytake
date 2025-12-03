from pydantic import BaseModel

from src.auth.models.user import User


class UserDto(BaseModel):
    id: int
    email: str

    name: str
    company: str | None

    server_host: str

    @staticmethod
    def map(user: User) -> "UserDto":
        return UserDto(
            id=user.id,
            email=user.email,
            name=user.name,
            company=user.company,
            server_host=user.server_host,
        )
