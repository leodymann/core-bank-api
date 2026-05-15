from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name:str="APIBank"
    environment:str="local"
    api_key:str="dev-2026"
    auth_enabled:bool=True
    rate_limit_enabled:bool=True
    rate_limit_requests:int=120
    rate_limit_window_seconds:int=60
    database_url:str="sqlite+aiosqlite:///./pagbank.db"
    database_pool_size:int=50
    database_max_overflow:int=100
    database_pool_timeout:int=10
    auto_create_tables:bool=False
    queue_backend:str="memory"
    redis_url:str="redis://localhost:6379/0"
    redis_transaction_queue_name:str="pagbank:transactions"
    queue_max_size:int=10_000
    queue_workers:int=8
    embedded_workers_enabled:bool=True
    transaction_timeout_seconds:int=30
    markdown_export_enabled:bool=True
    markdown_export_dir:str="./obsidian/transactions"

    model_config=SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
