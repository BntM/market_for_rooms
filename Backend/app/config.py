from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./market.db"
    APP_TITLE: str = "Market for Rooms"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    model_config = {"env_prefix": "MARKET_"}


settings = Settings()
