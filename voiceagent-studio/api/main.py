"""
VoiceAgent Studio — FastAPI backend
Handles: auth, agent CRUD, LiveKit token generation, KB upload, call logs
"""
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from core.config import get_settings
from core.logger import setup_logging, get_logger
from routers import agents, auth, calls, tokens, health, appointments

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=settings.app_env,
    )


# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_starting", env=settings.app_env)
    yield
    logger.info("api_shutdown")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoiceAgent Studio API",
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — only allow your frontend domain ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(auth.router,   prefix="/api/auth",   tags=["auth"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tokens.router, prefix="/api/tokens", tags=["tokens"])
app.include_router(calls.router,  prefix="/api/calls",  tags=["calls"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])


# ── Global exception handler — never leak stack traces ────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
