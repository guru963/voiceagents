from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client
from core.config import get_settings
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        result = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })
        return {
            "access_token": result.session.access_token,
            "user": result.user.email,
        }
    except Exception as e:
        logger.warning("login_failed", email=req.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
async def logout():
    return {"status": "logged_out"}
