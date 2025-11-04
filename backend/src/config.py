from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # for application
    app_name: str = "Caddy GUI"
    app_version: str = "0.1.0"
    debug: bool
    
    # for database
    database_url: str
    database_echo: bool
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore"
    )


settings = Settings()
