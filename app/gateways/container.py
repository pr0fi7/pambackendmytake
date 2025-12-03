# from dependency_injector import containers, providers
# from app.db.database import AsyncDatabase
# from app.config import settings
#
#
# class GatewayContainer(containers.DeclarativeContainer):
#     config = providers.Configuration()
#
#     print(settings.POSTGRESDB_URL)
#     async_session = providers.Singleton(
#         AsyncDatabase,
#         db_url=settings.POSTGRESDB_URL,
#     )
