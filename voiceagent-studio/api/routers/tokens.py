from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants
from core.config import get_settings
from core.logger import get_logger
import uuid

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class TokenRequest(BaseModel):
    agent_id: str
    user_name: str = "user"


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str


@router.post("/", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    """
    Generate a LiveKit room token for the frontend.
    NEVER expose LiveKit API secret to the browser — always generate server-side.
    """
    room_name = f"agent-{req.agent_id}-{uuid.uuid4().hex[:8]}"

    try:
        token = (
            AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(req.user_name)
            .with_name(req.user_name)
            .with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))
            .to_jwt()
        )

        logger.info("token_created", room=room_name, agent=req.agent_id)
        return TokenResponse(
            token=token,
            room_name=room_name,
            livekit_url=settings.livekit_url,
        )
    except Exception as e:
        logger.error("token_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create call token")
