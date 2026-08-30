from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DESKPILOT_", case_sensitive=False)

    environment: Literal["development", "test", "production"] = "development"
    service_name: str = "deskpilot-api"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
