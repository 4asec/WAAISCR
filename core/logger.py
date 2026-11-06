import logging
import re
import sys
from typing import Any

# Sensitive pattern regexes to mask
SECRET_PATTERNS = [
    re.compile(r'(AIzaSy[A-Za-z0-9_-]{33})', re.IGNORECASE), # Google Gemini API key
    re.compile(r'((?:bearer\s+|token\s+)[A-Za-z0-9_\-\.]{15,})', re.IGNORECASE),
    re.compile(r'([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})', re.IGNORECASE), # Emails
]

class SecretMaskingFormatter(logging.Formatter):
    """Logging formatter that automatically scrubs sensitive credentials and API keys."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        masked = original
        for pattern in SECRET_PATTERNS:
            masked = pattern.sub(r'***MASKED***', masked)
        return masked

def get_logger(name: str = "link_curator", level: int = logging.INFO) -> logging.Logger:
    """Returns a configured logger with secret scrubbing."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = SecretMaskingFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger
