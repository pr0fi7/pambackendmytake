from pydantic import BaseModel

from app.models.auth.user import ReadUserModel


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str


class LoginResponse(BaseModel):
    tokens: TokensResponse
    user: ReadUserModel
