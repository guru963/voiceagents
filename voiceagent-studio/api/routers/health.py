from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx
from core.config import get_settings
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Checks Supabase, Redis, and Groq are reachable.
    Returns 200 if all healthy, 503 if any dependency is down.
    Render/Railway use this to restart unhealthy containers.
    """
    status = {"supabase": False, "redis": False, "groq": False}

    async with httpx.AsyncClient(timeout=3.0) as client:
        # Supabase
        try:
            r = await client.get(
                f"{settings.supabase_url}/rest/v1/",
                headers={"apikey": settings.supabase_anon_key},
            )
            status["supabase"] = r.status_code < 500
        except Exception as e:
            logger.warning("health_supabase_fail", error=str(e))

        # Redis (Upstash ping)
        try:
            r = await client.get(
                f"{settings.upstash_redis_rest_url}/ping",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
            )
            status["redis"] = r.status_code == 200
        except Exception as e:
            logger.warning("health_redis_fail", error=str(e))

        # Groq reachability
        try:
            r = await client.get(
                "https://api.groq.com",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            )
            status["groq"] = r.status_code < 500
        except Exception as e:
            logger.warning("health_groq_fail", error=str(e))

    all_healthy = all(status.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ok" if all_healthy else "degraded", "checks": status},
    )
