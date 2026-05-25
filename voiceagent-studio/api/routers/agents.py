from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from supabase import create_client
from core.config import get_settings
from core.logger import get_logger
import uuid

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


def get_supabase():
    return create_client(settings.supabase_url, settings.supabase_service_key)


class AgentCreateRequest(BaseModel):
    name: str
    role: str
    industry: Literal["healthcare", "hospitality", "hr", "edtech", "custom"]
    language: Literal["en", "hi", "ta"] = "en"
    system_prompt: str
    tts_provider: Literal["edge_tts", "elevenlabs"] = "edge_tts"
    tools_enabled: list[str] = []


@router.get("/")
async def list_agents():
    """List all available agents."""
    try:
        supabase = get_supabase()
        result = supabase.table("agents").select("*").execute()
        return {"agents": result.data}
    except Exception as e:
        logger.error("list_agents_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch agents")


@router.post("/")
async def create_agent(req: AgentCreateRequest):
    """Create a new agent persona."""
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    try:
        supabase = get_supabase()
        result = supabase.table("agents").insert({
            "agent_id": agent_id,
            "name": req.name,
            "role": req.role,
            "industry": req.industry,
            "language": req.language,
            "system_prompt": req.system_prompt,
            "tts_provider": req.tts_provider,
            "tools_enabled": req.tools_enabled,
        }).execute()
        logger.info("agent_created", agent_id=agent_id)
        return {"agent_id": agent_id, "agent": result.data[0]}
    except Exception as e:
        logger.error("create_agent_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    try:
        supabase = get_supabase()
        result = supabase.table("agents").select("*").eq("agent_id", agent_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    try:
        supabase = get_supabase()
        supabase.table("agents").delete().eq("agent_id", agent_id).execute()
        return {"deleted": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/knowledge")
async def upload_knowledge(agent_id: str, file: UploadFile = File(...)):
    """Upload a PDF/text knowledge base for an agent."""
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = ["application/pdf", "text/plain"]

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files allowed")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    # Extract text
    text = ""
    if file.content_type == "text/plain":
        text = content.decode("utf-8")
    else:
        # PDF extraction
        import io
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = " ".join(page.extract_text() or "" for page in reader.pages)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # Trigger ingestion (import here to avoid circular)
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../agent"))
    from rag.knowledge_base import ingest_document
    await ingest_document(agent_id, text)

    logger.info("kb_uploaded", agent_id=agent_id, chars=len(text))
    return {"status": "ingested", "chars": len(text)}
