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
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()  # type: ignore


class MailerroSettings(BaseSettings):
    maileroo_base_url: str
    maileroo_domain_email: str
    mailerro_key: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


mailerro = MailerroSettings()  # type: ignore


class RedisSettings(BaseSettings):
    redis_url: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


redis_settings = RedisSettings()  # type: ignore


class TestSettings(BaseSettings):
    test_database_url: PostgresDsn

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


test_settings = TestSettings()  # type: ignore


class TwoFactorAuthenticationSettings(BaseSettings):
    two_factor_secret_key: str
    two_factor_salt: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


two_factor_auth = TwoFactorAuthenticationSettings()  # type: ignore
