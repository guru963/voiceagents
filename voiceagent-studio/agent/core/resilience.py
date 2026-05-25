from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import httpx
import logging
from core.logger import get_logger

logger = get_logger(__name__)

# Retry decorator for any external API call
# 3 attempts, exponential backoff: 1s → 2s → 4s
api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError, ConnectionError)),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)


class FallbackLLM:
    """
    Tries primary LLM (Groq). If it fails 3 times, falls over to Gemini.
    Never lets a rate limit or outage kill a live call.
    """

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
        self._consecutive_failures = 0
        self._failure_threshold = 3

    async def complete(self, messages: list, **kwargs):
        if self._consecutive_failures >= self._failure_threshold:
            logger.warning("llm_fallback_active", reason="consecutive_failures")
            try:
                result = await self.fallback.complete(messages, **kwargs)
                self._consecutive_failures = 0
                return result
            except Exception as e:
                logger.error("llm_fallback_failed", error=str(e))
                raise

        try:
            result = await self.primary.complete(messages, **kwargs)
            self._consecutive_failures = 0
            return result
        except Exception as e:
            self._consecutive_failures += 1
            logger.warning(
                "llm_primary_failed",
                error=str(e),
                failures=self._consecutive_failures,
            )
            if self._consecutive_failures >= self._failure_threshold:
                return await self.complete(messages, **kwargs)
            raise
