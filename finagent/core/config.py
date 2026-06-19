from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FinAgent AI"
    environment: str = "development"
    secret_key: str = "development-only-secret-key-change-me"
    database_url: str = "sqlite:///./finagent.db"
    redis_url: str = "redis://localhost:6379/0"
    chroma_path: Path = Path("data/chroma")
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    market_data_mode: str = "demo"
    jwt_expire_minutes: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])
    log_level: str = "INFO"

    @field_validator("secret_key")
    @classmethod
    def secure_production_secret(cls, value: str, info):
        if info.data.get("environment") == "production" and len(value) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters in production")
        return value

    @field_validator("database_url")
    @classmethod
    def use_psycopg_v3(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
