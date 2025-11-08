"""Configuration management using environment variables."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import pydantic_settings for Pydantic v2, fallback to pydantic for v1
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram Bot Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    # OpenAI API Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")

    # Google API Configuration
    google_credentials_file: str = Field(
        "credentials/credentials.json", env="GOOGLE_CREDENTIALS_FILE"
    )
    google_token_file: str = Field(
        "credentials/token.json", env="GOOGLE_TOKEN_FILE"
    )

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Bot Configuration
    default_timezone: str = Field("UTC", env="DEFAULT_TIMEZONE")
    enable_llm_extraction: bool = Field(True, env="ENABLE_LLM_EXTRACTION")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize settings and validate."""
        super().__init__(**kwargs)
        # Don't validate paths on init - they'll be checked when needed


# Global settings instance
settings = Settings()

