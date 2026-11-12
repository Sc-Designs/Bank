# pydantic_settings for .env
from pydantic_settings import BaseSettings, SettingsConfigDict


class env(BaseSettings):
    POSTGRES_CONFIG: str
    JWT_TOKEN: str
    ALGORITHM: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = env()
