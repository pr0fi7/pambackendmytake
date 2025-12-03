from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

metadata = MetaData(schema="pam")
DeclarativeBase = declarative_base(metadata=metadata)


class BaseEntity(DeclarativeBase):
    __abstract__ = True
    # pass

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
