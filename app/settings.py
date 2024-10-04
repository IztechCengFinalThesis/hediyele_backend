from typing import List

from pydantic_settings import BaseSettings
from yarl import URL


class Settings(BaseSettings):
    """App settings."""

    # Postgres
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_echo: bool = False
    postgres_max_overflow: int = 20
    postgres_pool_size: int = 10

    # CORS
    cors_origins: List[str] | None = None

    # Sentry
    sentry_dsn: str | None = None
    sentry_environment: str | None = None

    redis_dsn: str

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            path=f"/{self.postgres_db}",
        )


settings = Settings()
