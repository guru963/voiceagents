from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LiveKit
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    # STT
    deepgram_api_key: str = ""
    groq_api_key: str = ""

    # LLM fallback
    gemini_api_key: str = ""

    # DB
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: str

    # Redis
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    # App
    app_env: str = "development"
    secret_key: str
    frontend_url: str = "http://localhost:5173"

    # Observability
    sentry_dsn: str = ""

    class Config:
        env_file = "../.env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
