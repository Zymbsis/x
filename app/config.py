from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class TwitterApiIoSettings(BaseModel):
    api_key: str
    base_url: str = "https://api.twitterapi.io"
    rate_limit_enabled: bool = True
    period_sec: float = 5.0


class Settings(BaseSettings):
    environment: Literal["dev", "prod"] = "dev"

    api_key: str
    pg_database_url: str

    twitterapi_io: TwitterApiIoSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
SettingsDep = Annotated[Settings, Depends(get_settings)]
