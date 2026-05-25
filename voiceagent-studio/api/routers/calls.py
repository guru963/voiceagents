from fastapi import APIRouter, HTTPException
from supabase import create_client
from core.config import get_settings
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


def get_supabase():
    return create_client(settings.supabase_url, settings.supabase_service_key)


@router.get("/")
async def list_calls(agent_id: str = None, limit: int = 50):
    """Fetch call logs with latency metrics."""
    try:
        supabase = get_supabase()
        query = supabase.table("call_logs").select("*").order("created_at", desc=True).limit(limit)
        if agent_id:
            query = query.eq("agent_id", agent_id)
        result = query.execute()
        return {"calls": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
