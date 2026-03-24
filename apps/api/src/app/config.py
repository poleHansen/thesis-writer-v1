from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "thesis-writer-api"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    auto_create_tables: bool = True
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5432/thesis_writer"
    redis_url: str = "redis://127.0.0.1:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
