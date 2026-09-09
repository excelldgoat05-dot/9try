import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://gateway:secret@localhost/gateway"

    # Telegram
    ADDER_BOT_TOKEN: str = ""
    PAYWATCH_BOT_TOKEN: str = ""
    ADMIN_IDS: List[int] = []

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Payment
    PAYMENT_SESSION_TTL_MINUTES: int = 50
    MAX_UNDERPAID_ACCUMULATION_MINUTES: int = 1440
    CONFIRMATIONS_REQUIRED: dict = {
        "ethereum": 2,
        "bsc": 3,
        "polygon": 5,
        "solana": 1,
        "tron": 1,
    }

    # Blockchain RPC URLs
    ETH_RPC_URL: str = ""
    BSC_RPC_URL: str = ""
    POLYGON_RPC_URL: str = ""
    SOLANA_RPC_URL: str = ""
    TRON_RPC_URL: str = ""

    # Security
    ENCRYPTION_KEY: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
