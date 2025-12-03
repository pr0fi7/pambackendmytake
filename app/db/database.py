from typing import Iterable

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# class AsyncDatabase:
#     def __init__(self, db_url: str, use_ssl: bool = True) -> None:
#         connect_args = {}
#         if use_ssl:
#             ssl_context = ssl.create_default_context()
#             ssl_context.check_hostname = False  # optional
#             ssl_context.verify_mode = ssl.CERT_NONE  # optional for self-signed
#             connect_args["ssl"] = ssl_context
#
#         self._engine = create_async_engine(
#             db_url, poolclass=NullPool, echo=False, connect_args={"ssl": "require"}
#         )
#
#         self._session_factory = async_sessionmaker(
#             self._engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
#         )
#
#     @asynccontextmanager
#     async def session(self) -> AsyncContextManager[AsyncSession]:
#         async with self._session_factory() as session:
#             try:
#                 yield session
#             except Exception:
#                 await session.rollback()
#                 raise
#             finally:
#                 await session.close()


_url_object = URL.create(
    "postgresql+psycopg2",
    username=settings.DATABASE_USERNAME,
    password=settings.DATABASE_PASSWORD,
    host=settings.DATABASE_HOST,
    port=settings.DATABASE_PORT,
    database=settings.DATABASE_NAME,
)

_engine = create_engine(
    _url_object,
    pool_size=5,
    max_overflow=12,
    pool_pre_ping=True,
    pool_timeout=30,
    pool_recycle=3600,
)

# Session object to be used for executing queries
_session_maker = sessionmaker(bind=_engine, expire_on_commit=False)


class DatabaseConnector:
    def __init__(self):
        """
        Create a new session when connector is initialised
        """
        self.session = _session_maker()

    def __enter__(self):
        """
        This method is called when context manager is initialised for this object
        :return: The reference to its object
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        This method is called when context manager is closed
        It closes the connection to the database.
        """
        self.close()

    def close(self):
        """
        Method to close the connection to the database.
        :return:
        """
        self.session.close()

    def save_instances(self, instances: Iterable[object]):
        """
        Save a bunch of instances to the database
        :param instances: (Iterable[object]) - Iterable of objects to save to the database
        """
        self.session.add_all(instances)
        self.session.commit()

