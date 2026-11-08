import asyncio
import random
from typing import Any, Dict
import httpx
from adapters.channel.base import ChannelAdapter
from core.config import settings
from core.logger import get_logger

logger = get_logger("whatsapp_adapter")

class WhatsAppBaileysAdapter(ChannelAdapter):
    """Channel adapter connecting to the local Node.js Baileys microservice."""

    def __init__(self, gateway_url: str = "") -> None:
        self.gateway_url = (gateway_url or settings.whatsapp.gateway_url).rstrip("/")
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10.0)

    async def _anti_ban_delay(self) -> None:
        """Introduce small randomized delay between replies to prevent spam detection."""
        min_ms = settings.whatsapp.send_delay_min_ms
        max_ms = settings.whatsapp.send_delay_max_ms
        delay_sec = random.uniform(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay_sec)

    async def send_message(self, to: str, text: str) -> bool:
        await self._anti_ban_delay()
        try:
            url = f"{self.gateway_url}/send"
            response = await self._client.post(url, json={"to": to, "text": text})
            if response.status_code == 200:
                return True
            logger.error(f"Failed to send WA message to {to}: HTTP {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error calling WhatsApp gateway send endpoint: {e}")
            return False

    async def send_reaction(self, to: str, key_or_id: Any, emoji: str) -> bool:
        try:
            url = f"{self.gateway_url}/react"
            payload = {
                "to": to,
                "key": key_or_id if isinstance(key_or_id, dict) else {"id": key_or_id, "remoteJid": to},
                "emoji": emoji
            }
            response = await self._client.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending reaction '{emoji}' to {to}: {e}")
            return False

    async def get_status(self) -> Dict[str, Any]:
        try:
            url = f"{self.gateway_url}/status"
            response = await self._client.get(url)
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "error": f"HTTP {response.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Gateway process not reachable"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def is_connected(self) -> bool:
        status_info = await self.get_status()
        return status_info.get("status") == "connected"

    async def close(self) -> None:
        await self._client.aclose()
