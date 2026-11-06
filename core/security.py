import re
from typing import Optional
from core.config import settings, load_config
from core.logger import get_logger

logger = get_logger("security")

class SecurityGuard:
    """Handles whitelist enforcement and untrusted content sanitization."""

    @staticmethod
    def is_sender_allowed(sender_jid_or_phone: str) -> bool:
        """Check if sender is whitelisted. Ignores formatting and domain suffixes."""
        if not sender_jid_or_phone:
            return False
        # Remove @s.whatsapp.net, @lid, or @g.us
        raw = sender_jid_or_phone.split("@")[0]
        # Dynamically load latest whitelist so config.yaml updates apply immediately
        current_whitelist = load_config().whitelist
        allowed = current_whitelist.is_allowed(raw)
        if not allowed:
            logger.warning(f"Silently ignoring unauthorized message from: {raw}")
        return allowed

    @staticmethod
    def sanitize_untrusted_content(content: str, max_chars: int = 50000) -> str:
        """Sanitizes untrusted text (from links, PDFs, web) to prevent Prompt Injection attacks.
        
        Escapes tag boundaries and truncates excessive payloads.
        """
        if not content:
            return ""

        # Truncate content to safe limit
        safe_text = content[:max_chars]

        # Neutralize XML tags that might interfere with LLM boundary tags
        safe_text = safe_text.replace("</untrusted_content>", "&lt;/untrusted_content&gt;")
        safe_text = safe_text.replace("<untrusted_content>", "&lt;untrusted_content&gt;")
        safe_text = safe_text.replace("</system>", "&lt;/system&gt;")
        safe_text = safe_text.replace("<system>", "&lt;system&gt;")

        return safe_text

    @staticmethod
    def wrap_in_boundary(content: str) -> str:
        """Wraps untrusted content into strict XML boundaries for LLM prompts."""
        sanitized = SecurityGuard.sanitize_untrusted_content(content)
        return (
            "<untrusted_content>\n"
            f"{sanitized}\n"
            "</untrusted_content>"
        )
