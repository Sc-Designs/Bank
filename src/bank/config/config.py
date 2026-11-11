from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_CONFIG: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


env = Settings
settings = Settings()
