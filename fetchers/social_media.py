import re
from typing import Optional
import httpx
import instaloader
from fetchers.base import BaseFetcher, FetchResult
from fetchers.normalizer import URLNormalizer
from core.logger import get_logger

logger = get_logger("social_media_fetcher")

# Regex patterns for shortcodes and IDs
INSTA_SHORTCODE_REGEX = re.compile(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)', re.IGNORECASE)
TWITTER_STATUS_REGEX = re.compile(r'/status/(\d+)', re.IGNORECASE)

class SocialMediaFetcher(BaseFetcher):
    """Specialized fetcher for Social Media platforms: Instagram, TikTok, Twitter/X, YouTube."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._insta = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            save_metadata=False,
            quiet=True
        )

    def can_handle(self, url: str, platform: str) -> bool:
        return platform in ("instagram", "tiktok", "x", "youtube")

    async def _fetch_instagram(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch Instagram post caption using Instaloader, with oEmbed/Embed fallback."""
        m = INSTA_SHORTCODE_REGEX.search(norm_url)
        if not m:
            return None
        shortcode = m.group(1)

        # 1. Try Instaloader directly (retrieves full caption and author)
        try:
            logger.info(f"Fetching Instagram post '{shortcode}' via Instaloader...")
            post = instaloader.Post.from_shortcode(self._insta.context, shortcode)
            caption = (post.caption or "").strip()
            author = post.owner_username or "Instagram User"
            title = f"Instagram (@{author}): {caption[:60]}..." if caption else f"Instagram Post by @{author}"

            if caption:
                logger.info(f"Instaloader successfully extracted caption for {shortcode} ({len(caption)} chars)")
                return FetchResult(
                    url=url,
                    normalized_url=norm_url,
                    url_hash=url_hash,
                    platform="instagram",
                    title=title,
                    author=author,
                    text_content=caption,
                    status="success",
                    metadata={"shortcode": shortcode, "likes": getattr(post, "likes", 0)}
                )
        except Exception as e:
            logger.warning(f"Instaloader failed for shortcode '{shortcode}': {e}")

        # 2. Fallback: Parse embed captioned HTML
        try:
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(embed_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if res.status_code == 200:
                    text = res.text
                    # Search caption text in embed payload
                    cap_match = re.search(r'\\\"caption\\\":\{\\\"text\\\":\\\"(.*?)\\\"', text)
                    if cap_match:
                        raw_cap = cap_match.group(1).encode().decode("unicode_escape", errors="ignore")
                        if len(raw_cap.strip()) > 10:
                            return FetchResult(
                                url=url,
                                normalized_url=norm_url,
                                url_hash=url_hash,
                                platform="instagram",
                                title=f"Instagram Post: {raw_cap[:50]}...",
                                text_content=raw_cap.strip(),
                                status="success"
                            )
        except Exception as e:
            logger.debug(f"Instagram embed fallback failed: {e}")

        return None

    async def _fetch_tiktok(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch TikTok video info using official oEmbed API and yt-dlp."""
        try:
            # 1. Official TikTok oEmbed API
            oembed_url = f"https://www.tiktok.com/oembed?url={norm_url}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(oembed_url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title") or "TikTok Video"
                    author = data.get("author_name") or "TikTok Creator"
                    content = f"TikTok Creator: {author}\nVideo Title / Caption: {title}"
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform="tiktok",
                        title=f"TikTok - {author}: {title[:50]}",
                        author=author,
                        text_content=content,
                        status="success",
                        metadata=data
                    )
        except Exception as e:
            logger.warning(f"TikTok oEmbed failed: {e}")
        return None

    async def _fetch_twitter(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch Twitter / X post content via public oEmbed or FxTwitter API."""
        try:
            # 1. FxTwitter API
            m = TWITTER_STATUS_REGEX.search(norm_url)
            if m:
                status_id = m.group(1)
                fxtwitter_url = f"https://api.fxtwitter.com/status/{status_id}"
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(fxtwitter_url)
                    if resp.status_code == 200:
                        tweet_data = resp.json().get("tweet", {})
                        text = tweet_data.get("text", "")
                        author = tweet_data.get("author", {}).get("name", "X User")
                        screen_name = tweet_data.get("author", {}).get("screen_name", "")
                        if text:
                            return FetchResult(
                                url=url,
                                normalized_url=norm_url,
                                url_hash=url_hash,
                                platform="x",
                                title=f"Tweet oleh @{screen_name}: {text[:50]}...",
                                author=f"{author} (@{screen_name})",
                                text_content=f"Tweet oleh {author} (@{screen_name}):\n\n{text}",
                                status="success",
                                metadata=tweet_data
                            )
        except Exception as e:
            logger.debug(f"FxTwitter API failed: {e}")

        # 2. Official Twitter oEmbed fallback
        try:
            oembed_url = f"https://publish.twitter.com/oembed?url={norm_url}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(oembed_url)
                if resp.status_code == 200:
                    data = resp.json()
                    html_content = data.get("html", "")
                    clean_text = re.sub(r'<[^>]+>', ' ', html_content).strip()
                    author = data.get("author_name", "X User")
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform="x",
                        title=f"Tweet dari {author}",
                        author=author,
                        text_content=clean_text,
                        status="success",
                        metadata=data
                    )
        except Exception as e:
            logger.warning(f"Twitter oEmbed failed: {e}")

        return None

    async def _fetch_youtube(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch YouTube / Shorts video title & description via oEmbed & yt-dlp."""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={norm_url}&format=json"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(oembed_url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", "YouTube Video")
                    author = data.get("author_name", "YouTube Channel")
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform="youtube",
                        title=title,
                        author=author,
                        text_content=f"Video Title: {title}\nChannel: {author}\nURL: {norm_url}",
                        status="success",
                        metadata=data
                    )
        except Exception as e:
            logger.warning(f"YouTube oEmbed failed: {e}")
        return None

    async def fetch(self, url: str, platform: str) -> FetchResult:
        norm_url = URLNormalizer.normalize_url(url)
        url_hash = URLNormalizer.hash_url(norm_url)

        if platform == "instagram":
            result = await self._fetch_instagram(url, norm_url, url_hash)
            if result and result.is_usable:
                return result

        elif platform == "tiktok":
            result = await self._fetch_tiktok(url, norm_url, url_hash)
            if result and result.is_usable:
                return result

        elif platform == "x":
            result = await self._fetch_twitter(url, norm_url, url_hash)
            if result and result.is_usable:
                return result

        elif platform == "youtube":
            result = await self._fetch_youtube(url, norm_url, url_hash)
            if result and result.is_usable:
                return result

        return FetchResult(
            url=url,
            normalized_url=norm_url,
            url_hash=url_hash,
            platform=platform,
            status="need_fallback",
            error_message=f"Social media fetcher could not extract content from {platform}"
        )
