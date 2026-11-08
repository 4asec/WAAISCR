from typing import List, Optional
from fetchers.base import BaseFetcher, FetchResult
from fetchers.normalizer import URLNormalizer
from fetchers.public_api import PublicAPIFetcher
from fetchers.social_media import SocialMediaFetcher
from core.logger import get_logger

logger = get_logger("fetcher_chain")

class FetcherChain:
    """Manages an ordered chain of content fetchers, halting on first success."""

    def __init__(self, fetchers: Optional[List[BaseFetcher]] = None) -> None:
        self.fetchers: List[BaseFetcher] = fetchers or [
            SocialMediaFetcher(),
            PublicAPIFetcher()
        ]

    def add_fetcher(self, fetcher: BaseFetcher) -> None:
        """Dynamically append a new fetcher to the chain."""
        self.fetchers.append(fetcher)

    async def execute(self, raw_url: str) -> FetchResult:
        """Executes the fetcher chain stopping at the first successful extractor."""
        norm_url = URLNormalizer.normalize_url(raw_url)
        url_hash = URLNormalizer.hash_url(norm_url)
        platform = URLNormalizer.detect_platform(norm_url)

        last_result: Optional[FetchResult] = None

        for idx, fetcher in enumerate(self.fetchers):
            if fetcher.can_handle(norm_url, platform):
                logger.info(f"Attempting fetcher #{idx+1} ({fetcher.__class__.__name__}) for [{platform}] {norm_url}")
                try:
                    result = await fetcher.fetch(norm_url, platform)
                    last_result = result
                    if result.is_usable:
                        logger.info(f"Fetcher #{idx+1} succeeded for {norm_url}")
                        return result
                    else:
                        logger.debug(f"Fetcher #{idx+1} returned unusable result ({result.status}): {result.error_message}")
                except Exception as e:
                    logger.warning(f"Fetcher #{idx+1} raised exception: {e}")

        # If all fetchers in the chain failed or returned unusable data
        return last_result or FetchResult(
            url=raw_url,
            normalized_url=norm_url,
            url_hash=url_hash,
            platform=platform,
            status="need_fallback",
            error_message="All fetchers in chain exhausted without usable content"
        )
