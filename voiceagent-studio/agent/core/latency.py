import time
from dataclasses import dataclass, field
from typing import Optional
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LatencyRecord:
    call_id: str
    agent_id: str
    language: str
    stt_ms: Optional[float] = None
    llm_ms: Optional[float] = None
    tts_ms: Optional[float] = None
    tool_ms: Optional[float] = None
    total_ms: Optional[float] = None
    tool_called: Optional[str] = None
    transcript: Optional[str] = None
    _start: float = field(default_factory=time.perf_counter, repr=False)

    def finish(self):
        self.total_ms = round((time.perf_counter() - self._start) * 1000, 2)
        logger.info(
            "pipeline_latency",
            call_id=self.call_id,
            agent_id=self.agent_id,
            language=self.language,
            stt_ms=self.stt_ms,
            llm_ms=self.llm_ms,
            tts_ms=self.tts_ms,
            tool_ms=self.tool_ms,
            total_ms=self.total_ms,
            tool_called=self.tool_called,
        )
        return self


class LatencyTracker:
    """Context-manager-based latency tracker for each pipeline stage."""

    def __init__(self, record: LatencyRecord, stage: str):
        self.record = record
        self.stage = stage
        self._t = None

    def __enter__(self):
        self._t = time.perf_counter()
        return self

    def __exit__(self, *_):
        elapsed = round((time.perf_counter() - self._t) * 1000, 2)
        setattr(self.record, f"{self.stage}_ms", elapsed)
