from logging.config import fileConfig

import sqlalchemy as sa
from alembic import context

from app.config import settings
from migrations.utils import create_database_if_not_exists
from app.entities import *

# target_metadata = DeclarativeBase.metadata
# Alembic config object
config = context.config
fileConfig(config.config_file_name)
target_metadata = BaseEntity.metadata

print(target_metadata)
print("Metadata object id:", id(BaseEntity.metadata))
print("Tables in metadata:", BaseEntity.metadata.tables.keys())
# Ensure the database exists before running migrations
create_database_if_not_exists(settings.DATABASE_NAME)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = (
        "postgresql+asyncpg://"
        + f"{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@"
        + f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_schemas=True,
        version_table_schema="pam",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode using your DatabaseConnector."""
    # Use the raw engine from your DatabaseConnector
    from app.db.database import _engine  # your engine already configured

    # Ensure the schema exists before running migrations
    with _engine.connect() as connection:
        connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS pam"))
        connection.commit()  # commit schema creation if needed

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
            version_table_schema="pam",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
