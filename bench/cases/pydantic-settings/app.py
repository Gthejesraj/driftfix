from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = "sqlite://"
    debug: bool = False
    api_key: str = Field(..., env="SERVICE_API_KEY")

    class Config:
        env_prefix = "APP_"


def load() -> Settings:
    return Settings()
