"""SCENTIQ Application Configuration.
Type-safe settings using Pydantic Settings v2.
"""
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py is at: <repo_root>/apps/api/app/core/config.py
# parents[0] = core
# parents[1] = app
# parents[2] = api
# parents[3] = apps
# parents[4] = <repo_root>
ROOT_DIR = Path(__file__).resolve().parents[4]
DEV_SQLITE_PATH = ROOT_DIR / "data" / "scentiq_dev.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "SCENTIQ"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # Database
    DATABASE_URL: str = f"sqlite:///{DEV_SQLITE_PATH.as_posix()}"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        if v and v.startswith("sqlite"):
            if ":memory:" in v:
                return "sqlite:///:memory:"
            DEV_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{DEV_SQLITE_PATH.as_posix()}"
        return v

    # Security
    SECRET_KEY: str = "dev_insecure_secret_key_change_in_production_min32chars_scentiq2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Regional & Currency context
    DEFAULT_COUNTRY: str = "IN"
    DEFAULT_CURRENCY: str = "INR"

    # AI Advisor (EPIC-11)
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""


settings = Settings()
