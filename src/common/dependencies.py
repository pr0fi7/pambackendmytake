from typing import Any, Generator

from src.common.db.database_connector import DatabaseConnector


def get_database_connector_dependency() -> Generator[DatabaseConnector | Any, Any, None]:
    """
    Dependency to inject a database connector object.
    :return: (DatabaseConnector) - Generator of the connector object to the database
    """
    with DatabaseConnector() as db:
        yield db
