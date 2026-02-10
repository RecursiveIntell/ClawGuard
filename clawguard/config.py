"""ClawGuard configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ANTHROPIC_API_KEY: str = ""
    CLAWGUARD_MODEL: str = "claude-sonnet-4-5-20250929"
    DATABASE_URL: str = "postgresql://localhost:5432/clawguard"
    REDIS_URL: str = "redis://localhost:6379/0"
    LOG_LEVEL: str = "INFO"
    MAX_SKILL_SIZE_MB: int = 10

    model_config = {"env_prefix": "CLAWGUARD_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
