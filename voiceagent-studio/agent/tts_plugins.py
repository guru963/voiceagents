"""
Custom TTS plugins for LiveKit agents.
  - KokoroTTS: Free, local, high-quality English voices (no API key needed)
  - EdgeTTS:   Free Microsoft neural voices for Hindi / Tamil / multilingual
"""

import asyncio
import io
import numpy as np
from livekit.agents import tts, APIConnectOptions
from livekit import rtc

from core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CONN_OPTIONS = APIConnectOptions()


# ── Kokoro TTS ────────────────────────────────────────────────────────────────

class KokoroTTS(tts.TTS):
    """
    Local Kokoro TTS — best free English quality.
    Runs entirely on CPU/GPU, no API key required.
    """

    def __init__(self, voice: str = "af_heart", speed: float = 1.0):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._voice = voice
        self._speed = speed
        self._pipeline = None

    def _ensure_pipeline(self):
        if self._pipeline is None:
            from kokoro import KPipeline
            self._pipeline = KPipeline(lang_code="a")  # 'a' = American English
            logger.info("kokoro_pipeline_loaded")
        return self._pipeline

    def synthesize(self, text: str, *, conn_options=DEFAULT_CONN_OPTIONS):
        return _KokoroStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options,
        )


class _KokoroStream(tts.ChunkedStream):
    def __init__(self, *, tts_instance: KokoroTTS, input_text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts_instance, input_text=input_text, conn_options=conn_options)
        self._tts_instance = tts_instance

    async def _run(self, output_emitter):
        loop = asyncio.get_event_loop()
        pipeline = self._tts_instance._ensure_pipeline()
        text = self._input_text
        voice = self._tts_instance._voice
        speed = self._tts_instance._speed

        def _generate():
            chunks = []
            for result in pipeline(text, voice=voice, speed=speed):
                chunks.append(result.audio)
            return chunks

        try:
            audio_chunks = await loop.run_in_executor(None, _generate)

            from livekit.agents.utils import shortuuid
            req_id = shortuuid()

            output_emitter.initialize(
                request_id=req_id,
                sample_rate=24000,
                num_channels=1,
                mime_type="audio/pcm",
            )

            for samples in audio_chunks:
                # Convert PyTorch Tensor to NumPy array if needed
                if hasattr(samples, "numpy"):
                    samples = samples.cpu().numpy() if hasattr(samples, "cpu") else samples.numpy()
                elif not isinstance(samples, np.ndarray):
                    samples = np.array(samples)

                # samples is a numpy float32 array at 24 kHz
                pcm_int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
                output_emitter.push(pcm_int16.tobytes())

            output_emitter.flush()
        except Exception as e:
            logger.error("kokoro_tts_error", error=str(e))
            raise


# ── Fallback TTS ──────────────────────────────────────────────────────────────

class FallbackTTS(tts.TTS):
    """
    A TTS wrapper that attempts to use a primary TTS (e.g. Kokoro) and falls back
    to a secondary TTS (e.g. Edge TTS) if the primary fails during synthesis.
    """

    def __init__(self, primary: tts.TTS, fallback: tts.TTS):
        super().__init__(
            capabilities=primary.capabilities,
            sample_rate=primary.sample_rate,
            num_channels=primary.num_channels,
        )
        self._primary = primary
        self._fallback = fallback

    def synthesize(self, text: str, *, conn_options=DEFAULT_CONN_OPTIONS):
        return _FallbackStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options,
        )


class _FallbackStream(tts.ChunkedStream):
    def __init__(self, *, tts_instance: FallbackTTS, input_text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts_instance, input_text=input_text, conn_options=conn_options)
        self._tts_instance = tts_instance

    async def _run(self, output_emitter):
        primary = self._tts_instance._primary
        fallback = self._tts_instance._fallback
        req_id = None
        
        try:
            logger.info("fallback_tts: attempting primary TTS synthesis")
            primary_stream = primary.synthesize(self._input_text, conn_options=self._conn_options)
            
            initialized = False
            async for ev in primary_stream:
                if not initialized:
                    req_id = ev.request_id
                    output_emitter.initialize(
                        request_id=req_id,
                        sample_rate=primary.sample_rate,
                        num_channels=primary.num_channels,
                        mime_type="audio/pcm",
                    )
                    initialized = True
                output_emitter.push(ev.frame.data.tobytes())
                
            if initialized:
                output_emitter.flush()
                logger.info("fallback_tts: primary TTS synthesis succeeded")
                return
            else:
                raise RuntimeError("primary TTS did not yield any audio frames")
                
        except Exception as e:
            logger.warning("fallback_tts: primary TTS failed, falling back to secondary", error=str(e))
            
            fallback_stream = fallback.synthesize(self._input_text, conn_options=self._conn_options)
            initialized = False
            async for ev in fallback_stream:
                if not initialized:
                    if not req_id:
                        from livekit.agents.utils import shortuuid
                        req_id = shortuuid()
                    output_emitter.initialize(
                        request_id=req_id,
                        sample_rate=fallback.sample_rate,
                        num_channels=fallback.num_channels,
                        mime_type="audio/pcm",
                    )
                    initialized = True
                output_emitter.push(ev.frame.data.tobytes())
                
            if initialized:
                output_emitter.flush()
                logger.info("fallback_tts: fallback TTS synthesis succeeded")
            else:
                raise RuntimeError("fallback TTS did not yield any audio frames")



# ── Edge TTS ──────────────────────────────────────────────────────────────────

# Voice presets for Indian languages
EDGE_VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",      # Hindi female
    "ta": "ta-IN-PallaviNeural",     # Tamil female
    "en": "en-IN-NeerjaNeural",      # English (Indian accent) female
}


class EdgeTTS(tts.TTS):
    """
    Microsoft Edge TTS — best free Hindi / Tamil neural voices.
    Uses the edge-tts library (no API key needed).
    """

    def __init__(self, voice: str | None = None, language: str = "en"):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._voice = voice or EDGE_VOICE_MAP.get(language, EDGE_VOICE_MAP["en"])
        self._language = language

    def synthesize(self, text: str, *, conn_options=DEFAULT_CONN_OPTIONS):
        return _EdgeStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options,
        )


class _EdgeStream(tts.ChunkedStream):
    def __init__(self, *, tts_instance: EdgeTTS, input_text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts_instance, input_text=input_text, conn_options=conn_options)
        self._tts_instance = tts_instance

    async def _run(self, output_emitter):
        import edge_tts

        try:
            communicate = edge_tts.Communicate(
                self._input_text,
                voice=self._tts_instance._voice,
            )

            # Collect MP3 bytes from edge-tts
            mp3_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_buffer.write(chunk["data"])

            mp3_buffer.seek(0)

            # Decode MP3 → PCM using soundfile
            import soundfile as sf
            samples, sr = sf.read(mp3_buffer, dtype="float32")

            # Convert to mono if stereo
            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            # Resample to 24 kHz if needed
            if sr != 24000:
                from fractions import Fraction
                ratio = Fraction(24000, sr)
                target_len = int(len(samples) * ratio)
                indices = np.linspace(0, len(samples) - 1, target_len)
                samples = np.interp(indices, np.arange(len(samples)), samples).astype(np.float32)

            # Convert to int16 PCM
            pcm_int16 = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)

            from livekit.agents.utils import shortuuid
            req_id = shortuuid()

            output_emitter.initialize(
                request_id=req_id,
                sample_rate=24000,
                num_channels=1,
                mime_type="audio/pcm",
            )

            output_emitter.push(pcm_int16.tobytes())
            output_emitter.flush()

        except Exception as e:
            logger.error("edge_tts_error", error=str(e))
            raise
