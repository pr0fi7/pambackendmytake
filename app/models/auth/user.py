from datetime import datetime
from typing import Optional

from passlib.apps import custom_app_context as pwd_context

from app.models.base.abstract_model import AbstractModel


class ReadUserModel(AbstractModel):
    id: int
    email: str
    name: str
    company: Optional[str] = None
    server_host: Optional[str] = None
    created_date: datetime


class CheckUserPasswordModel(AbstractModel):
    id: int
    email: str
    password_hash: str

    def check_password(self, password) -> bool:
        return pwd_context.verify(password, self.password_hash)


class CreateUserModel(AbstractModel):
    email: str
    password_hash: str
    name: str
    company: Optional[str] = None
    server_host: Optional[str] = None
    created_date: datetime

