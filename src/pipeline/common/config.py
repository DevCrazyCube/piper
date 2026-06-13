"""Runtime configuration (pydantic-settings). Loaded once from the environment / .env.

Secrets are SecretStr so they don't leak into logs or reprs. Nothing here is ever
committed — see .env.example and ADR-0008 for key custody.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", extra="ignore")

    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "aegis"
    db_user: str = "aegis"
    db_password: SecretStr = SecretStr("")

    # Base64-encoded 32-byte AES-256 key for application-layer field encryption.
    master_key: SecretStr = SecretStr("")

    datasets_dir: Path = Path("/data/datasets")
    log_level: str = "INFO"

    @property
    def sqlalchemy_dsn(self) -> str:
        pwd = self.db_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def psycopg_conninfo(self) -> str:
        pwd = self.db_password.get_secret_value()
        return (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={self.db_user} password={pwd}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
