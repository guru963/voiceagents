import asyncio
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from core.config import get_settings
from core.logger import get_logger
from core.resilience import api_retry

logger = get_logger(__name__)
settings = get_settings()

# Local embedding model — completely free, no API calls
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("loading_embedding_model", model="all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def embed_text(text: str) -> list[float]:
    """Run embedding in thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    model = get_embedding_model()
    embedding = await loop.run_in_executor(None, model.encode, text)
    return embedding.tolist()


async def ingest_document(agent_id: str, text: str, chunk_size: int = 500):
    """Chunk a document and store embeddings in Supabase pgvector."""
    supabase = get_supabase()
    words = text.split()
    chunks = [
        " ".join(words[i : i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

    logger.info("ingesting_document", agent_id=agent_id, chunks=len(chunks))

    for i, chunk in enumerate(chunks):
        embedding = await embed_text(chunk)
        supabase.table("knowledge_chunks").insert({
            "agent_id": agent_id,
            "content": chunk,
            "embedding": embedding,
            "chunk_index": i,
        }).execute()

    logger.info("ingestion_complete", agent_id=agent_id)


async def search_kb(agent_id: str, query: str, top_k: int = 3) -> str:
    """Semantic search over agent's knowledge base. Returns top_k chunks as context."""
    try:
        supabase = get_supabase()
        query_embedding = await embed_text(query)

        result = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "agent_id_filter": agent_id,
            "match_count": top_k,
        }).execute()

        if not result.data:
            return ""

        chunks = [row["content"] for row in result.data]
        context = "\n\n---\n\n".join(chunks)
        logger.debug("kb_search", agent_id=agent_id, results=len(chunks))
        return context

    except Exception as e:
        logger.error("kb_search_failed", error=str(e), agent_id=agent_id)
        return ""
