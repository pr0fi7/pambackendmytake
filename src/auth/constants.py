import datetime

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    AUTH_SECRET_KEY: str

    HARMIX_API_KEY: str


env_config = EnvironmentConfig()

# Name to as header key for api key authorization
API_KEY_NAME = 'api-key'

# Issuer of the bearer token
TOKEN_ISSUER = 'api.harmix.ai'

# Lifetime of tokens
ACCESS_TOKEN_LIFETIME = datetime.timedelta(days=14)
REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=30)
