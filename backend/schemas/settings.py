from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = APP_ROOT / "pyproject.toml"
ENV_PATH = APP_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="FILTRI_",
        extra="ignore",
    )

    database_path: str = Field(default="data/filtri.db", min_length=1)
    database_url: str | None = None

    @property
    def sqlite_database_path(self) -> Path:
        return APP_ROOT / self.database_path

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.sqlite_database_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
