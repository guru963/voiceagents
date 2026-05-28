

import asyncio
import re
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
from tts_plugins import KokoroTTS, EdgeTTS, FallbackTTS

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


# ── Text sanitizer — strip leaked function-call syntax from LLM output ────────
_FUNC_CALL_RE = re.compile(
    r'<function=\w+>.*?</function>',
    re.DOTALL,
)

def _strip_function_calls(text: str) -> str:
    """Remove <function=...>...</function> patterns that small LLMs leak into text."""
    cleaned = _FUNC_CALL_RE.sub('', text).strip()
    # Also strip orphaned angle-bracket fragments
    cleaned = re.sub(r'</?function[^>]*>', '', cleaned).strip()
    return cleaned


# ── CleanAgent — Agent subclass with output sanitization ──────────────────────
from collections.abc import AsyncIterable

class CleanAgent(Agent):
    """Agent that filters out function-call syntax from LLM text before TTS."""

    async def tts_node(self, text: AsyncIterable[str], model_settings):
        async def _filtered():
            async for chunk in text:
                cleaned = _strip_function_calls(chunk)
                if cleaned:
                    yield cleaned
        async for frame in Agent.default.tts_node(self, _filtered(), model_settings):
            yield frame

    async def transcription_node(self, text, model_settings):
        async for chunk in Agent.default.transcription_node(self, text, model_settings):
            if isinstance(chunk, str):
                cleaned = _strip_function_calls(chunk)
                if cleaned:
                    yield cleaned
            else:
                yield chunk


class CallTools:
    def __init__(self, room, agent_id: str, tools_enabled: list[str]):
        self.room = room
        self.agent_id = agent_id
        self.tools_enabled = tools_enabled or []

    async def _send_booking_status(self, type_: str, details: dict):
        """Send a JSON payload to the frontend via WebRTC data channel."""
        try:
            from datetime import datetime
            import json
            payload = json.dumps({
                "type": type_,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                **details
            })
            await self.room.local_participant.publish_data(
                payload.encode('utf-8')
            )
            logger.info("published_webrtc_data", type=type_, payload=payload)
        except Exception as e:
            logger.error("failed_to_publish_webrtc_data", error=str(e))

    def _parse_date_and_time(self, date_str: str, time_str: str = None) -> tuple[str, str | None]:
        """Parse natural language date and time into database-friendly formats."""
        from datetime import datetime, timedelta
        from dateutil import parser
        
        # Use midnight as default time to avoid inheriting current system minutes/seconds
        default_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        parsed_date = default_dt.date()
        parsed_time = None
        
        cleaned_date_str = date_str.lower().strip() if date_str else ""
        if cleaned_date_str == "today":
            parsed_date = datetime.now().date()
        elif cleaned_date_str == "tomorrow":
            parsed_date = (datetime.now() + timedelta(days=1)).date()
        elif date_str:
            try:
                dt = parser.parse(date_str, default=default_dt)
                parsed_date = dt.date()
                has_time = any(m in date_str.lower() for m in ['am', 'pm', ':', "o'clock", 'noon', 'midnight'])
                if has_time:
                    parsed_time = dt.strftime('%I:%M %p')
            except Exception:
                pass
                
        if time_str:
            try:
                t_dt = parser.parse(time_str, default=default_dt)
                parsed_time = t_dt.strftime('%I:%M %p')
            except Exception:
                parsed_time = time_str
                
        return parsed_date.isoformat(), parsed_time

    async def _persist_appointment(self, data: dict):
        """Save appointment to Supabase appointments table."""
        try:
            from supabase import create_client
            settings = get_settings()
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            supabase.table("appointments").insert(data).execute()
            logger.info("appointment_persisted", ref_id=data.get("ref_id"))
        except Exception as e:
            logger.warning("appointment_persist_failed", error=str(e))

    @llm.function_tool(description="Book appointment. Only call after patient confirms name, department, doctor, preferred date, and optional preferred time.")
    async def book_appointment(
        self,
        patient_name: str,
        department: str,
        preferred_date: str,
        preferred_time: str = "",
        doctor_name: str = "",
    ) -> str:
        if "book_appointment" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        from datetime import datetime
        logger.info("tool_book_appointment", patient=patient_name, dept=department, date=preferred_date, time=preferred_time)
        ref_id = f"APL{datetime.now().strftime('%Y%m%d%H%M')}"
        
        date_iso, time_formatted = self._parse_date_and_time(preferred_date, preferred_time)
        
        await self._send_booking_status("booking_confirmed", {
            "category": "hospital",
            "patient_name": patient_name,
            "department": department,
            "preferred_date": date_iso,
            "preferred_time": time_formatted,
            "doctor_name": doctor_name or "Dr. Anita Sharma",
            "ref_id": ref_id
        })
        
        await self._persist_appointment({
            "agent_id": self.agent_id,
            "category": "hospital",
            "ref_id": ref_id,
            "guest_name": patient_name,
            "title": f"{department} — {doctor_name or 'Dr. Anita Sharma'}",
            "appointment_date": date_iso,
            "appointment_time": time_formatted,
            "details": {"department": department, "doctor_name": doctor_name or "Dr. Anita Sharma"},
            "status": "confirmed",
        })

        time_part = f" at {time_formatted}" if time_formatted else ""
        return (
            f"Appointment confirmed for {patient_name} in {department} "
            f"on {date_iso}{time_part} with {doctor_name or 'Dr. Anita Sharma'}. Reference ID: {ref_id}."
        )

    @llm.function_tool(description="Check doctor slots. Only call after patient specifies department and date.")
    async def check_doctor_availability(self, department: str, date: str) -> str:
        if "check_doctor_availability" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        logger.info("tool_check_availability", dept=department, date=date)
        from rag.doctors_data import query_availability, get_slots_list
        
        date_iso, _ = self._parse_date_and_time(date)
        slots = get_slots_list(department, date_iso)
        
        await self._send_booking_status("availability_checked", {
            "category": "hospital",
            "department": department,
            "date": date_iso,
            "slots": slots
        })
        
        return query_availability(department, date_iso)

    @llm.function_tool(description="Get department location and details. Only when patient asks.")
    async def get_department_info(self, department: str) -> str:
        if "get_department_info" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        from rag.doctors_data import get_dept_details
        return get_dept_details(department)

    @llm.function_tool(description="Book a restaurant table at the hotel restaurant.")
    async def book_restaurant(
        self,
        guest_name: str,
        restaurant: str,
        date: str,
        time: str,
        guests: int,
    ) -> str:
        if "book_restaurant" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        from datetime import datetime
        logger.info("tool_book_restaurant", guest=guest_name, restaurant=restaurant)
        ref_id = f"LLP{datetime.now().strftime('%H%M%S')}"
        
        date_iso, time_formatted = self._parse_date_and_time(date, time)
        
        await self._send_booking_status("booking_confirmed", {
            "category": "restaurant",
            "guest_name": guest_name,
            "restaurant": restaurant,
            "date": date_iso,
            "time": time_formatted,
            "guests": guests,
            "ref_id": ref_id
        })
        
        await self._persist_appointment({
            "agent_id": self.agent_id,
            "category": "restaurant",
            "ref_id": ref_id,
            "guest_name": guest_name,
            "title": f"Table at {restaurant}",
            "appointment_date": date_iso,
            "appointment_time": time_formatted,
            "details": {"restaurant": restaurant, "guests": guests},
            "status": "confirmed",
        })

        return (
            f"Table reserved for {guests} at {restaurant} on {date_iso} at {time_formatted}. "
            f"Confirmation Reference: {ref_id}."
        )

    @llm.function_tool(description="Check hotel suite or room availability.")
    async def check_room_availability(self, room_type: str, check_in: str, check_out: str) -> str:
        if "check_room_availability" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        mock_rooms = {
            "deluxe": "Available — ₹12,000/night, sea view, king bed",
            "suite": "2 suites available — ₹28,000/night, private balcony",
            "premier": "Available — ₹18,000/night, city view",
        }
        desc = mock_rooms.get(room_type.lower(), "Available — ₹15,000/night")
        
        await self._send_booking_status("availability_checked", {
            "category": "hotel",
            "room_type": room_type,
            "check_in": check_in,
            "check_out": check_out,
            "description": desc
        })
        
        return f"Room {room_type} availability check: {desc}."

    @llm.function_tool(description="Get hotel amenity details like spa, pool, gym, wifi.")
    async def get_amenities(self, amenity: str = "") -> str:
        if "get_amenities" not in self.tools_enabled:
            return "This tool is not enabled for this agent."
            
        amenities = {
            "spa": "Tattva Spa — Floor 5, open 7 AM to 10 PM. Treatments from ₹3,500.",
            "pool": "Infinity pool — Rooftop, open 6 AM to 9 PM. Towels provided.",
            "gym": "Fitness centre — Floor 4, open 24 hours. Personal trainer available.",
            "wifi": "Complimentary high-speed WiFi throughout the property. Password at check-in.",
            "parking": "Valet parking available. Complimentary for hotel guests.",
        }
        if amenity:
            return amenities.get(amenity.lower(), "Please contact the concierge desk for details.")
        return "We offer: " + ", ".join(amenities.keys())


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
            # Check disk space to prevent Rust process panic on low disk space
            import os
            import shutil
            home = os.path.expanduser("~")
            _, _, free_bytes = shutil.disk_usage(home)
            if free_bytes < 400 * 1024 * 1024:  # 400 MB
                raise RuntimeError(
                    f"Insufficient disk space on {home} (only {free_bytes / (1024*1024):.1f}MB free). "
                    "Need at least 400MB to download Kokoro TTS model."
                )

            tts_instance = KokoroTTS(voice="af_heart", speed=1.0)
            # Pre-load the pipeline now so we fail fast if model can't download
            tts_instance._ensure_pipeline()
            logger.info("tts_provider", provider="kokoro", language=persona.language)
            return FallbackTTS(tts_instance, EdgeTTS(language=persona.language.value))
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
        prompt += f"\n{kb_context}"
    prompt += "\n\nIMPORTANT: Keep every reply under 2 sentences. Be warm but extremely concise — this is a live phone call."
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

    if persona.industry == "healthcare":
        from rag.doctors_data import DOCTORS_DATABASE
        dept_names = ", ".join(d.capitalize() for d in DOCTORS_DATABASE.keys())
        kb_context = f"\nDepartments: {dept_names}. Use tools to look up slots."

    system_prompt = build_system_prompt(persona, kb_context)

    # ── Load conversation history from Redis ──────────────────────────────────
    history = await get_history(call_id)

    # ── Build chat context (limit history to save tokens) ─────────────────────
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="system", content=system_prompt)
    for msg in history[-6:]:
        chat_ctx.add_message(role=msg["role"], content=msg["content"])

    # ── Build LLM ─────────────────────────────────────────────────────────────
    agent_llm = groq.LLM(
        model="llama-3.1-8b-instant",
        api_key=settings.groq_api_key,
        temperature=0.3,
        max_completion_tokens=300,  # Must be enough for tool-call JSON output
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

    # ── Tool / Function context ───────────────────────────────────────────────
    agent_tools = []
    if persona.tools_enabled:
        tools_instance = CallTools(ctx.room, persona.agent_id, persona.tools_enabled)
        agent_tools = llm.find_function_tools(tools_instance)
        logger.info("function_context_initialized", agent_id=persona.agent_id, tools=persona.tools_enabled)

    # ── Create Agent ──────────────────────────────────────────────────────────
    agent = CleanAgent(
        instructions=system_prompt,
        llm=agent_llm,
        stt=build_stt(persona),
        tts=build_tts(persona),
        vad=silero.VAD.load(),
        chat_ctx=chat_ctx,
        tools=agent_tools,
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
        messages = chat_ctx.messages() if callable(chat_ctx.messages) else chat_ctx.messages
        await save_history(call_id, [
            {"role": str(m.role), "content": str(m.content)}
            for m in messages[-20:]
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
