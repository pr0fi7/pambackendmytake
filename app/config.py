import datetime
from os import environ

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environs: dict = {}  # noqa: RUF012

    ENVIRONMENT: str

    # DEBUG: bool

    AUTH_SECRET_KEY: str
    HARMIX_API_KEY: str
    COMPOSIO_API_KEY: str
    TOKEN_ISSUER: str = "api.harmix.ai"

    # Lifetime of tokens
    ACCESS_TOKEN_LIFETIME: datetime.timedelta = datetime.timedelta(minutes=30)
    REFRESH_TOKEN_LIFETIME: datetime.timedelta = datetime.timedelta(days=30)

    # Database configuration.
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str

    WORKING_DIR: str

    CORS_ALLOWED_ORIGINS: list = [
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
    CORS_ALLOWED_ORIGIN_REGEX: str = r"https://.*\.ngrok-free\.app"

    AGENT_API: bool = True
    CENTRAL_API_USER_ID: list = [1, 2]

    DOCS_PUBLIC_PATHS: set[str] = {
        "/docs",
        "/docs/",
        "/docs/index.html",
        "/redoc",
        "/openapi.json",
    }

    VM_NAME: str
    VM_IP: str
    VM_ZONE: str
    VM_SCRIPTS_LOCATION: str = "/usr/local/sbin/pam-scripts"
    REDIS_URL: str


settings = Settings()  # type: ignore
settings.environs = environ  # type: ignore
