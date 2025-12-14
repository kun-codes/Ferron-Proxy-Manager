from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ferron Proxy Manager"
    app_version: str = "0.1.0"
    debug: bool
    
    database_url: str
    database_echo: bool
    
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
