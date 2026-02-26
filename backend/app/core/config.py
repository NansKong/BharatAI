"""
BharatAI Backend – Application Settings
Uses pydantic-settings for environment-based config with full type validation.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), str(REPO_DIR / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "BharatAI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-to-random-32-char-string"

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL_FEED: int = 900  # 15 min
    REDIS_CACHE_TTL_LEADERBOARD: int = 600  # 10 min
    REDIS_CACHE_TTL_OPPORTUNITIES: int = 300  # 5 min

    # ── JWT ───────────────────────────────────────────────────────────────
    JWT_PRIVATE_KEY_PATH: str = "./jwt_private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./jwt_public.pem"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_V2_PATH: Optional[str] = None  # For key rotation

    # ── Google OAuth2 ─────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── AI / ML ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL_CLASSIFIER: str = "facebook/bart-large-mnli"
    HUGGINGFACE_MODEL_EMBEDDINGS: str = "sentence-transformers/all-MiniLM-L6-v2"
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.6
    FAISS_INDEX_PATH: str = "./data/faiss.index"

    # ── Celery ────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_SCRAPE_INTERVAL_MINUTES: int = 30

    # ── Elasticsearch ─────────────────────────────────────────────────────
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_OPPORTUNITIES: str = "bharatai_opportunities"

    # ── File Storage ──────────────────────────────────────────────────────
    STORAGE_BACKEND: str = "minio"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_RESUMES: str = "bharatai-resumes"
    MINIO_BUCKET_UPLOADS: str = "bharatai-uploads"
    MAX_RESUME_SIZE_MB: int = 5

    # ── Email ─────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "BharatAI"
    SMTP_FROM_EMAIL: str = "noreply@bharatai.in"
    EMAIL_ENABLED: bool = False

    # ── Feature Flags ─────────────────────────────────────────────────────
    FEATURE_AI_CLASSIFICATION: bool = False
    FEATURE_PERSONALIZED_FEED: bool = False
    FEATURE_INCOSCORE_ENGINE: bool = False
    FEATURE_COMMUNITY: bool = False
    FEATURE_APP_ASSISTANCE: bool = False
    FEATURE_BROWSER_AUTOMATION: bool = False

    # ── Rate Limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_ANON: int = 60
    RATE_LIMIT_AUTH: int = 300
    RATE_LIMIT_AUTOFILL_PER_HOUR: int = 20

    # ── Proxy for scraping ────────────────────────────────────────────────
    PROXY_LIST: str = ""

    # ── Observability ─────────────────────────────────────────────────────
    PROMETHEUS_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "bharatai-backend"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # ── Computed properties ───────────────────────────────────────────────
    @property
    def jwt_private_key(self) -> str:
        return Path(self.JWT_PRIVATE_KEY_PATH).read_text()

    @property
    def jwt_public_key(self) -> str:
        return Path(self.JWT_PUBLIC_KEY_PATH).read_text()

    @property
    def proxy_list(self) -> List[str]:
        return [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @field_validator("CLASSIFICATION_CONFIDENCE_THRESHOLD")
    @classmethod
    def validate_confidence_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                "CLASSIFICATION_CONFIDENCE_THRESHOLD must be between 0 and 1"
            )
        return v

    @field_validator("DATABASE_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int) -> int:
        if v < 1:
            raise ValueError("DATABASE_POOL_SIZE must be at least 1")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


# Convenience: settings instance used across the app
settings = get_settings()
