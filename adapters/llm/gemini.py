import asyncio
import json
from typing import Any, Dict, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from adapters.llm.base import LLMProvider
from core.config import settings
from core.logger import get_logger

logger = get_logger("gemini_provider")
T = TypeVar("T", bound=BaseModel)

class GeminiProvider(LLMProvider):
    """Google Gemini API Provider with structured JSON output and rate limiter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        rpm: Optional[int] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None
    ) -> None:
        cfg = settings.llm
        super().__init__(
            rpm=rpm or cfg.rate_limit.requests_per_minute,
            max_retries=max_retries or cfg.max_retries,
            timeout_seconds=timeout_seconds or cfg.timeout_seconds
        )
        self.api_key = api_key or cfg.api_key or ""
        self.model = model or cfg.model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client = httpx.AsyncClient(timeout=float(self.timeout_seconds))

    def _get_endpoint(self) -> str:
        clean_model = self.model.replace("models/", "")
        return f"{self.base_url}/models/{clean_model}:generateContent?key={self.api_key}"

    async def _execute_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gemini API call with exponential backoff and rate limiter."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured. Please add it to your .env or config.yaml.")

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            await self.rate_limiter.acquire()
            try:
                response = await self._client.post(self._get_endpoint(), json=payload)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (429, 503):
                    delay = (2 ** attempt) + 0.5
                    logger.warning(f"Gemini API returned HTTP {response.status_code}. Retrying in {delay:.1f}s (Attempt {attempt}/{self.max_retries})...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    error_msg = f"Gemini API error HTTP {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                delay = (2 ** attempt)
                logger.warning(f"Gemini network/timeout error: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Exceeded max retries calling Gemini API. Last error: {last_error}")

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = await self._execute_with_retry(payload)
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return "Maaf, tidak ada tanggapan yang dihasilkan oleh model."
            text = candidates[0]["content"]["parts"][0]["text"]
            return text
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise RuntimeError(f"Unexpected Gemini API response structure: {data}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None
    ) -> T:
        """Generate structured JSON conforming strictly to the provided Pydantic model."""
        json_schema = schema.model_json_schema()

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": json_schema
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = await self._execute_with_retry(payload)
        try:
            raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed_dict = json.loads(raw_json_str)
            return schema.model_validate(parsed_dict)
        except Exception as e:
            logger.error(f"Failed to parse structured response into schema {schema.__name__}: {e}")
            raise

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            result = await self.generate_text("Reply with 'OK'")
            return bool(result)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    async def close(self) -> None:
        await self._client.aclose()
