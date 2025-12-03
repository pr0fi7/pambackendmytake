from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

metadata = MetaData(schema="pam")
DeclarativeBase = declarative_base(metadata=metadata)


class BaseModel(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
