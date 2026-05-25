

import asyncio
import uuid
import sentry_sdk

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    Agent,
    AgentSession,
    RoomInputOptions,
)
from livekit.plugins import deepgram, groq, silero

from core.config import get_settings
from core.logger import get_logger, setup_logging
from core.session import get_history, save_history, delete_session
from personas.models import (
    AgentPersona,
    HOSPITAL_PERSONA,
    HOSPITAL_PERSONA_HINDI,
    HOTEL_PERSONA,
    HOTEL_PERSONA_TAMIL,
    Language,
    TTSProvider,
)
from rag.knowledge_base import search_kb
from tts_plugins import KokoroTTS, EdgeTTS

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.2)

# ── Persona registry ──────────────────────────────────────────────────────────
PERSONA_REGISTRY: dict[str, AgentPersona] = {
    HOSPITAL_PERSONA.agent_id: HOSPITAL_PERSONA,
    HOSPITAL_PERSONA_HINDI.agent_id: HOSPITAL_PERSONA_HINDI,
    HOTEL_PERSONA.agent_id: HOTEL_PERSONA,
    HOTEL_PERSONA_TAMIL.agent_id: HOTEL_PERSONA_TAMIL,
}


def build_stt(persona: AgentPersona):
    """Deepgram streaming STT (primary) or Groq Whisper (fallback)."""
    lang_code = persona.language.value  # "en", "hi", "ta"
    if settings.deepgram_api_key:
        dg_lang_map = {
            "en": "en-US",
            "hi": "hi-IN",
            "ta": "ta-IN",
        }
        dg_lang = dg_lang_map.get(lang_code, "en-US")
        logger.info("stt_provider", provider="deepgram", language=dg_lang)
        return deepgram.STT(api_key=settings.deepgram_api_key, language=dg_lang)
    logger.info("stt_provider", provider="groq_whisper", language=lang_code)
    return groq.STT(api_key=settings.groq_api_key, language=lang_code)


def build_tts(persona: AgentPersona):
    """
    TTS selection based on persona config:
      English  → Kokoro TTS (free, local, high-quality)
                 Falls back to Edge TTS if Kokoro model can't load (e.g. low disk space)
      Hindi    → Edge TTS (free Microsoft neural voices)
      Tamil    → Edge TTS (free Microsoft neural voices)
      Fallback → Groq TTS (requires API key)
    """
    if persona.tts_provider == TTSProvider.KOKORO:
        try:
            tts_instance = KokoroTTS(voice="af_heart", speed=1.0)
            # Pre-load the pipeline now so we fail fast if model can't download
            tts_instance._ensure_pipeline()
            logger.info("tts_provider", provider="kokoro", language=persona.language)
            return tts_instance
        except Exception as e:
            logger.warning(
                "kokoro_unavailable_falling_back_to_edge_tts",
                error=str(e),
                language=persona.language,
            )
            # Fall through to Edge TTS
            return EdgeTTS(language=persona.language.value)

    if persona.tts_provider == TTSProvider.EDGE_TTS:
        logger.info("tts_provider", provider="edge_tts", language=persona.language)
        return EdgeTTS(language=persona.language.value)

    # Fallback to Groq TTS
    logger.info("tts_provider", provider="groq_tts_fallback", language=persona.language)
    return groq.TTS(
        model="playai-tts-arabic",
        voice="Celeste-PlayAI",
        api_key=settings.groq_api_key,
    )


def build_system_prompt(persona: AgentPersona, kb_context: str = "") -> str:
    """Assemble final system prompt with persona + optional KB context."""
    prompt = persona.system_prompt
    if kb_context:
        prompt += f"\n\n--- Knowledge Base Context ---\n{kb_context}"
    prompt += (
        "\n\nIMPORTANT: Keep responses concise — 2 sentences max — "
        "since this is a live voice call. Never use markdown, bullet points, "
        "numbers, or special characters in your response."
    )
    return prompt


async def entrypoint(ctx: JobContext):
    """Called by LiveKit for every incoming call room."""
    call_id = str(uuid.uuid4())[:8]
    logger.info("call_started", call_id=call_id, room=ctx.room.name)

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # ── Load persona from room name or Supabase DB ────────────────────────────
    # Room name format: "agent-{agent_id}-{random}"
    # e.g. "agent-apollo-receptionist-f3e7cc49"
    parts = ctx.room.name.split("-")
    # agent_id is everything between first and last segment
    agent_id = "-".join(parts[1:-1]) if len(parts) > 2 else "apollo-receptionist"
    
    persona = PERSONA_REGISTRY.get(agent_id)
    if not persona:
        try:
            from supabase import create_client
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            result = supabase.table("agents").select("*").eq("agent_id", agent_id).execute()
            if result.data:
                agent_data = result.data[0]
                try:
                    lang = Language(agent_data.get("language", "en"))
                except ValueError:
                    lang = Language.ENGLISH

                try:
                    tts_prov = TTSProvider(agent_data.get("tts_provider", "edge_tts"))
                except ValueError:
                    tts_prov = TTSProvider.EDGE_TTS

                persona = AgentPersona(
                    agent_id=agent_data["agent_id"],
                    name=agent_data["name"],
                    role=agent_data["role"],
                    industry=agent_data["industry"],
                    language=lang,
                    tts_provider=tts_prov,
                    system_prompt=agent_data["system_prompt"],
                    kb_enabled=agent_data.get("kb_enabled", False),
                    tools_enabled=agent_data.get("tools_enabled") or [],
                )
                logger.info("persona_loaded_from_db", call_id=call_id, agent_id=agent_id, language=persona.language)
        except Exception as e:
            logger.error("failed_to_load_persona_from_db", error=str(e), agent_id=agent_id)

    if not persona:
        persona = HOSPITAL_PERSONA
        logger.info("persona_loaded_fallback", call_id=call_id, agent_id=agent_id)

    # ── Load KB context if enabled ────────────────────────────────────────────
    kb_context = ""
    if persona.kb_enabled:
        kb_context = await search_kb(persona.agent_id, "welcome greeting help")

    system_prompt = build_system_prompt(persona, kb_context)

    # ── Load conversation history from Redis ──────────────────────────────────
    history = await get_history(call_id)

    # ── Build chat context ────────────────────────────────────────────────────
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="system", content=system_prompt)
    for msg in history:
        chat_ctx.add_message(role=msg["role"], content=msg["content"])

    # ── Build LLM ─────────────────────────────────────────────────────────────
    agent_llm = groq.LLM(
        model="llama-3.1-8b-instant",
        api_key=settings.groq_api_key,
        temperature=0,
    )

    # ── Greeting by language ──────────────────────────────────────────────────
    greeting_map = {
        Language.ENGLISH: f"Hello! I'm {persona.name}. How may I assist you today?",
        Language.HINDI: f"Namaste! Main {persona.name} hoon. Aap kaise madad kar sakti hoon?",
        Language.TAMIL: f"Vanakkam! Naan {persona.name}. Ungalukku epadi udavi seiyalaam?",
    }
    greeting = greeting_map.get(
        persona.language,
        f"Hello! I'm {persona.name}. How may I assist you today?"
    )

    # ── Create Agent ──────────────────────────────────────────────────────────
    agent = Agent(
        instructions=system_prompt,
        llm=agent_llm,
        stt=build_stt(persona),
        tts=build_tts(persona),
        vad=silero.VAD.load(),
        chat_ctx=chat_ctx,
    )

    # ── Start AgentSession ────────────────────────────────────────────────────
    session = AgentSession()

    session.on("user_input_transcribed")(
        lambda transcript: logger.info(
            "user_spoke", call_id=call_id, text=str(transcript)[:100]
        )
    )

    session.on("agent_state_changed")(
        lambda state: logger.info("agent_state", call_id=call_id, state=str(state))
    )

    try:
        await session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(),
        )

        # Send greeting
        await session.generate_reply(instructions=greeting)

        # Keep alive until room closes
        await asyncio.sleep(3600)

    finally:
        # Save final history and clean up
        await save_history(call_id, [
            {"role": str(m.role), "content": str(m.content)}
            for m in chat_ctx.messages[-20:]
        ])
        await delete_session(call_id)
        logger.info("call_ended", call_id=call_id)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
            ws_url=settings.livekit_url,
        )
    )
