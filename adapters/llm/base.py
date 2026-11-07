import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from core.logger import get_logger

logger = get_logger("llm_base")
T = TypeVar("T", bound=BaseModel)

class RateLimiter:
    """Token-bucket rate limiter for managing API request and token throughput."""

    def __init__(self, rpm: int = 15, tpm: int = 1000000) -> None:
        self.rpm = rpm
        self.tpm = tpm
        self.request_timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if request rate limit is exceeded."""
        async with self._lock:
            now = time.monotonic()
            # Retain only timestamps within the last 60 seconds
            self.request_timestamps = [t for t in self.request_timestamps if now - t < 60.0]

            if len(self.request_timestamps) >= self.rpm:
                oldest = self.request_timestamps[0]
                sleep_time = max(0.1, 60.0 - (now - oldest) + 0.1)
                logger.warning(f"Rate limit reached ({len(self.request_timestamps)}/{self.rpm} RPM). Throttling for {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
                # Re-clean timestamps after waking up
                now = time.monotonic()
                self.request_timestamps = [t for t in self.request_timestamps if now - t < 60.0]

            self.request_timestamps.append(time.monotonic())

class LLMProvider(ABC):
    """Abstract interface for LLM backends (Gemini, Ollama, etc.)."""

    def __init__(self, rpm: int = 15, max_retries: int = 3, timeout_seconds: int = 45) -> None:
        self.rate_limiter = RateLimiter(rpm=rpm)
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate free-form text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None
    ) -> T:
        """Generate validated Pydantic model response."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify API connectivity and key validity."""
        pass
