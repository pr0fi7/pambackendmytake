from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    AGENT_API: bool = False
    CENTRAL_API_USER_ID: list[int] = []


env_config = EnvironmentConfig()
