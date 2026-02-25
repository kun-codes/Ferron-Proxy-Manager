from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ferron Proxy Manager"
    # below line is used in tbump.toml, update its regex there when updating changing structure of line here
    app_version: str = "0.1.0"
    production: bool = True  # in case user misses to specify this, a value of True is safer for production

    database_url: str
    database_echo: bool

    ferron_container_name: str

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
