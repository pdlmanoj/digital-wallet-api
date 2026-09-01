from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_version: str
    debug: bool
    database_url: PostgresDsn
    environement: Literal["dev", "testing"] = "dev"
    access_token_secret_key: str
    algorithm: str
    access_token_expire_time: int = 10  # min
    refresh_token_secret_key: str
    refresh_token_expire_time: int = 1  # day
    maileroo_base_url: str
    maileroo_domain_email: str
    mailerro_key: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()  # type: ignore


class RedisSettings(BaseSettings):
    redis_url: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

redis_settings = RedisSettings()  # type: ignore