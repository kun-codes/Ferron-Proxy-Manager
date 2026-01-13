from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    # usage of this is discouraged: https://docs.pydantic.dev/latest/concepts/fields/
    secret_key: str = Field(description="Secret key for signing access tokens")
    refresh_secret_key: str = Field(description="Secret key for signing refresh tokens")
    signup_disabled: bool = Field(description="Whether to disable user signup")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"), env_prefix="AUTH_", extra="ignore"
    )


auth_settings = AuthSettings()
