from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ChannelAdapter(ABC):
    """Abstract interface for messaging channel gateways (WhatsApp, Telegram, etc)."""

    @abstractmethod
    async def send_message(self, to: str, text: str) -> bool:
        """Send a plain text message to target recipient."""
        pass

    @abstractmethod
    async def send_reaction(self, to: str, key_or_id: Any, emoji: str) -> bool:
        """Send an emoji reaction to a specific message."""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get live connection status: 'connected', 'reconnecting', or 'logged_out'."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if channel is ready to send/receive messages."""
        pass
