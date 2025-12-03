from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router
from app.config import settings
from app.container import ApplicationContainer
from app.middlewares import ErrorLoggingMiddleware, HarmixAPIKeyMiddleware


def create_application() -> FastAPI:
    server_app = FastAPI(
        title="Harmix PAM API",
        description="Backend API for PAM services",
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=settings.CORS_ALLOWED_ORIGINS,
                allow_origin_regex=settings.CORS_ALLOWED_ORIGIN_REGEX,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
    )

    container = ApplicationContainer()
    server_app.container = container  # type: ignore

    server_app.add_middleware(ErrorLoggingMiddleware)
    server_app.add_middleware(HarmixAPIKeyMiddleware)

    server_app.include_router(router)

    return server_app


app = create_application()
