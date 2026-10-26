from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    decision_cutoff_local_time: str = "09:00"
    timezone: str = "Europe/London"
    data_dir: str = "data"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    decision_start: date = date(2026, 1, 1)
    decision_end: date = date(2026, 1, 31)

    @property
    def delivery_start(self) -> date:
        return self.decision_start + timedelta(days=1)

    @property
    def delivery_end(self) -> date:
        return self.decision_end + timedelta(days=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
