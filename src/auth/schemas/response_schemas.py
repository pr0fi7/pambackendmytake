from pydantic import BaseModel

from src.auth.schemas.user_dto import UserDto


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str


class LoginResponse(BaseModel):
    tokens: TokensResponse
    user: UserDto
