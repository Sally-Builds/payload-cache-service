"""Service configuration, loaded from environment variables.

Every setting can be overridden with a CACHE_-prefixed env var, e.g.
CACHE_DATABASE_URL or CACHE_TRANSFORMER_LATENCY_SECONDS.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CACHE_")

    database_url: str = "sqlite+aiosqlite:///./cache.db"
    transformer_latency_seconds: float = 0.05
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
