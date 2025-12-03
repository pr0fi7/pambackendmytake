import psycopg2
from psycopg2 import sql, OperationalError, errors

from app.config import settings


def create_database_if_not_exists(database_name: str):
    """
    Synchronously create a PostgreSQL database if it does not exist.
    Uses a direct psycopg2 connection to 'postgres' database for creation.
    """
    try:
        # Try connecting to the target database
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            user=settings.DATABASE_USERNAME,
            password=settings.DATABASE_PASSWORD,
            dbname=database_name,
        )
    except OperationalError as e:
        # If database does not exist, create it
        if isinstance(e.__cause__, errors.InvalidCatalogName):
            # Connect to default 'postgres' DB to create the target DB
            sys_conn = psycopg2.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                user=settings.DATABASE_USERNAME,
                password=settings.DATABASE_PASSWORD,
                dbname="postgres",
            )
            sys_conn.autocommit = True
            cur = sys_conn.cursor()
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database_name),
                    sql.Identifier(settings.DATABASE_USERNAME),
                )
            )
            cur.close()
            sys_conn.close()
        else:
            raise
    else:
        # Database exists, just close connection
        conn.close()
