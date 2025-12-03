from datetime import datetime

from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.common.models.base_model import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    created_date: Mapped[datetime] = mapped_column(default=func.now())
    email: Mapped[str]
    password_hash: Mapped[str | None]

    name: Mapped[str]
    company: Mapped[str | None]

    server_host: Mapped[str]

    def set_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password) -> bool:
        return pwd_context.verify(password, self.password_hash)
