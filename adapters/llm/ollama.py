from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from adapters.llm.base import LLMProvider
from core.logger import get_logger

logger = get_logger("ollama_stub")
T = TypeVar("T", bound=BaseModel)

class OllamaProvider(LLMProvider):
    """Stub provider for local Ollama LLM execution."""

    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "llama3.2") -> None:
        super().__init__(rpm=60)
        self.host = host
        self.model = model

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        logger.info(f"[Ollama Stub] Would query local model {self.model}")
        return f"[Ollama Stub] Responding to: {prompt[:40]}..."

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None
    ) -> T:
        raise NotImplementedError("Ollama structured output stub is ready for future expansion.")

    async def health_check(self) -> bool:
        return True
