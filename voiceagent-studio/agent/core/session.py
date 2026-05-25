import json
import httpx
from core.config import get_settings
from core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

SESSION_TTL = 3600  # 1 hour — always set TTL, never leak state


async def get_history(call_id: str) -> list[dict]:
    """Retrieve conversation history from Upstash Redis."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.upstash_redis_rest_url}/get/session:{call_id}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                timeout=3.0,
            )
            data = resp.json()
            if data.get("result"):
                return json.loads(data["result"])
    except Exception as e:
        logger.warning("redis_get_failed", call_id=call_id, error=str(e))
    return []


async def save_history(call_id: str, history: list[dict]):
    """Save conversation history with TTL."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.upstash_redis_rest_url}/setex/session:{call_id}/{SESSION_TTL}",
                headers={
                    "Authorization": f"Bearer {settings.upstash_redis_rest_token}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(json.dumps(history)),
                timeout=3.0,
            )
    except Exception as e:
        logger.warning("redis_save_failed", call_id=call_id, error=str(e))


async def delete_session(call_id: str):
    """Clean up session when call ends."""
    try:
        async with httpx.AsyncClient() as client:
            await client.get(
                f"{settings.upstash_redis_rest_url}/del/session:{call_id}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                timeout=3.0,
            )
        logger.info("session_deleted", call_id=call_id)
    except Exception as e:
        logger.warning("redis_delete_failed", call_id=call_id, error=str(e))
