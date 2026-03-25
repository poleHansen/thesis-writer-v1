from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ai-ppt-studio-api"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_allow_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    auto_create_tables: bool = True
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5432/ai_ppt_studio"
    redis_url: str = "redis://127.0.0.1:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
