from typing import Iterable

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from src.common import constants

_url_object = URL.create(
    "postgresql+psycopg2",
    username=constants.env_config.DATABASE_USERNAME,
    password=constants.env_config.DATABASE_PASSWORD,
    host=constants.env_config.DATABASE_HOST,
    port=constants.env_config.DATABASE_PORT,
    database=constants.env_config.DATABASE_NAME,
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
