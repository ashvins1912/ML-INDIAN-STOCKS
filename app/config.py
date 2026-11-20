from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quant:quant_dev_password@localhost/quant_db"
    redis_url: str = "redis://localhost:6379/0"
    influx_url: str = "http://localhost:8086"
    influx_org: str = "quant_org"
    influx_bucket: str = "market_raw"
    influx_token: str = "dev-influx-token-change-me"
    fernet_key: str = ""
    frontend_url: str = "http://localhost:8501"
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
