from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class FetchResult(BaseModel):
    url: str
    normalized_url: str
    url_hash: str
    platform: str
    title: Optional[str] = None
    author: Optional[str] = None
    text_content: str = ""
    status: str = "success"  # "success" | "need_fallback" | "failed"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_usable(self) -> bool:
        return self.status == "success" and bool(self.text_content.strip())

class BaseFetcher(ABC):
    """Abstract interface for all content fetchers in the pipeline."""

    @abstractmethod
    def can_handle(self, url: str, platform: str) -> bool:
        """Determine if this fetcher handles the given URL / platform."""
        pass

    @abstractmethod
    async def fetch(self, url: str, platform: str) -> FetchResult:
        """Attempt to retrieve readable text content from URL."""
        pass
