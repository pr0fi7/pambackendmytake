from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import auth_router
from src.messages.router import router as messages_router

from app.api import v1
from app.container import ApplicationContainer
from app import dependencies

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "https://develop.d1istgnjgx59dn.amplifyapp.com",
    "https://pam.harmix.ai",
    "https://uat.pam.harmix.ai",
    "https://pam-api.harmix.ai",
    "https://uat.pam-api.harmix.ai",
    "https://prod-pam-backend-api-577902591259.europe-west1.run.app",
    "https://uat-pam-backend-api-577902591259.europe-west1.run.app",
]
origins_regex = r"https://.*\.ngrok-free\.app"

# Initialize the dependency injection container
container = ApplicationContainer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wire the container and set it for dependencies
    container.wire()
    dependencies.set_container(container)
    yield
    # Unwire when app shuts down
    container.unwire()


app = FastAPI(
    lifespan=lifespan,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=origins_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=['*'],
        )
    ]
)

# Attach container to app state
app.container = container

app.include_router(auth_router, tags=["auth"])
app.include_router(messages_router, tags=["messages"])

app.include_router(v1)
