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
    model_config = SettingsConfigDict(env_prefix="PIPER_", env_file=".env", extra="ignore")

    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "piper"

    # Admin/superuser creds — used ONLY for migrations + role bootstrap.
    db_user: str = "piper"
    db_password: SecretStr = SecretStr("")

    # Runtime application role — NOSUPERUSER, NOBYPASSRLS (so RLS actually applies).
    # Falls back to the admin user only if no app password is configured.
    app_user: str = "piper_app"
    app_password: SecretStr = SecretStr("")

    # Base64-encoded 32-byte AES-256 master key; per-purpose subkeys are HKDF-derived.
    master_key: SecretStr = SecretStr("")

    datasets_dir: Path = Path("/data/datasets")
    log_level: str = "INFO"

    def _dsn(self, user: str, pwd: str) -> str:
        return f"postgresql+psycopg://{user}:{pwd}@{self.db_host}:{self.db_port}/{self.db_name}"

    def _conninfo(self, user: str, pwd: str) -> str:
        return (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={user} password={pwd}"
        )

    @property
    def sqlalchemy_dsn(self) -> str:
        """Admin DSN — used by Alembic (migrations need superuser: extensions, roles)."""
        return self._dsn(self.db_user, self.db_password.get_secret_value())

    @property
    def admin_conninfo(self) -> str:
        return self._conninfo(self.db_user, self.db_password.get_secret_value())

    @property
    def psycopg_conninfo(self) -> str:
        """Runtime DSN — the non-superuser app role when configured, else admin fallback."""
        app_pwd = self.app_password.get_secret_value()
        if app_pwd:
            return self._conninfo(self.app_user, app_pwd)
        return self.admin_conninfo


@lru_cache
def get_settings() -> Settings:
    return Settings()
