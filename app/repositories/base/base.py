from typing import Generic, Type, TypeVar

from sqlalchemy.exc import IntegrityError

from app.db.database import DatabaseConnector

# T represents a SQLAlchemy model type
T = TypeVar("T")


class BaseSessionRepository(Generic[T]):
    model: Type[T] | None = None

    def __init__(self, model: Type[T] | None = None):
        self.model = model or self.model
        if self.model is None:
            raise RuntimeError("Repository must define a model")

    def create(self, **kwargs) -> T:
        with DatabaseConnector() as db:
            instance = self.model(**kwargs)
            db.session.add(instance)
            db.session.commit()
            db.session.refresh(instance)
            return instance

    def get(self, **kwargs) -> T | None:
        with DatabaseConnector() as db:
            return db.session.query(self.model).filter_by(**kwargs).first()

    def list(self, limit: int | None = None, offset: int | None = 0, **kwargs) -> list[T]:
        with DatabaseConnector() as db:
            query = db.session.query(self.model).filter_by(**kwargs).offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()

    def update(self, update_data: dict, **kwargs) -> T | None:
        with DatabaseConnector() as db:
            query = db.session.query(self.model).filter_by(**kwargs)
            instance = query.first()
            if not instance:
                return None
            for key, value in update_data.items():
                setattr(instance, key, value)
            db.session.commit()
            db.session.refresh(instance)
            return instance

    def delete(self, **kwargs) -> None:
        with DatabaseConnector() as db:
            query = db.session.query(self.model).filter_by(**kwargs)
            try:
                query.delete(synchronize_session=False)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                raise Exception(
                    "Object is related to other objects and cannot be deleted"
                )
