from typing import Any, Dict
from adapters.channel.base import ChannelAdapter
from core.logger import get_logger

logger = get_logger("whatsapp_cloud_stub")

class WhatsAppCloudAdapter(ChannelAdapter):
    """Stub adapter for official Meta WhatsApp Cloud API.
    
    Allows swapping without modifying the core system or modules.
    """

    def __init__(self, phone_number_id: str = "", access_token: str = "") -> None:
        self.phone_number_id = phone_number_id
        self.access_token = access_token

    async def send_message(self, to: str, text: str) -> bool:
        logger.info(f"[Cloud API Stub] Would send message to {to}: {text[:50]}...")
        # Future implementation using graph.facebook.com/v20.0/{phone_number_id}/messages
        return True

    async def send_reaction(self, to: str, key_or_id: Any, emoji: str) -> bool:
        logger.info(f"[Cloud API Stub] Would react {emoji} to message {key_or_id}")
        return True

    async def get_status(self) -> Dict[str, Any]:
        return {"status": "stub", "provider": "WhatsApp Cloud API"}

    async def is_connected(self) -> bool:
        return True
