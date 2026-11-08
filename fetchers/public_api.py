import json
from typing import Optional
from bs4 import BeautifulSoup
import httpx
import trafilatura
from fetchers.base import BaseFetcher, FetchResult
from fetchers.normalizer import URLNormalizer
from core.logger import get_logger

logger = get_logger("public_fetcher")

class PublicAPIFetcher(BaseFetcher):
    """Fetches articles, OpenGraph metadata, and public API data without requiring logins."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id,en-US;q=0.9,en;q=0.8"
        }

    def can_handle(self, url: str, platform: str) -> bool:
        # Generic public fetcher handles any general web link, github, reddit
        return platform in ("web", "github", "reddit", "news") or True

    async def _fetch_reddit(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch reddit post content via .json endpoint."""
        try:
            json_url = norm_url.rstrip("/") + ".json"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(json_url, headers={"User-Agent": "Mozilla/5.0 LinkCurator/0.1"})
                if resp.status_code == 200:
                    data = resp.json()
                    post_data = data[0]["data"]["children"][0]["data"]
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    author = post_data.get("author", "")
                    content = f"{title}\n\n{selftext}"
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform="reddit",
                        title=title,
                        author=author,
                        text_content=content.strip(),
                        status="success"
                    )
        except Exception as e:
            logger.debug(f"Reddit JSON fetch failed, will fallback to HTML: {e}")
        return None

    async def _fetch_github(self, url: str, norm_url: str, url_hash: str) -> Optional[FetchResult]:
        """Fetch GitHub repo description & README metadata if public."""
        try:
            # Check if url matches github.com/{owner}/{repo}
            parts = [p for p in norm_url.split("github.com/")[-1].split("/") if p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(api_url, headers={"User-Agent": "LinkCurator-Bot"})
                    if resp.status_code == 200:
                        data = resp.json()
                        title = f"{owner}/{repo}: {data.get('description', '')}"
                        stars = data.get("stargazers_count", 0)
                        language = data.get("language", "Unknown")
                        topics = ", ".join(data.get("topics", []))
                        content = f"Repository: {owner}/{repo}\nDescription: {data.get('description')}\nLanguage: {language}\nStars: {stars}\nTopics: {topics}"
                        return FetchResult(
                            url=url,
                            normalized_url=norm_url,
                            url_hash=url_hash,
                            platform="github",
                            title=title,
                            author=owner,
                            text_content=content,
                            status="success",
                            metadata={"stars": stars, "language": language}
                        )
        except Exception as e:
            logger.debug(f"GitHub API fetch failed, will fallback to HTML: {e}")
        return None

    async def fetch(self, url: str, platform: str) -> FetchResult:
        norm_url = URLNormalizer.normalize_url(url)
        url_hash = URLNormalizer.hash_url(norm_url)

        # Platform-specific fast paths
        if platform == "reddit":
            reddit_res = await self._fetch_reddit(url, norm_url, url_hash)
            if reddit_res and reddit_res.is_usable:
                return reddit_res

        if platform == "github":
            gh_res = await self._fetch_github(url, norm_url, url_hash)
            if gh_res and gh_res.is_usable:
                return gh_res

        # General HTTP Article / Webpage fetch via trafilatura + BeautifulSoup
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(norm_url, headers=self.headers)
                if response.status_code != 200:
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform=platform,
                        status="need_fallback",
                        error_message=f"HTTP status {response.status_code}"
                    )

                html = response.text

                # 1. Trafilatura main body extraction
                extracted_text = trafilatura.extract(
                    html,
                    include_links=False,
                    include_images=False,
                    output_format="txt"
                )

                # 2. BeautifulSoup OpenGraph & Title fallback
                soup = BeautifulSoup(html, "html.parser")
                title = ""
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()

                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    title = og_title["content"].strip()

                og_desc = soup.find("meta", property="og:description")
                description = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""

                combined_content = extracted_text or description
                if not combined_content and len(html) > 100:
                    # Strip basic text from body tags
                    body = soup.find("body")
                    if body:
                        combined_content = body.get_text(separator="\n", strip=True)[:4000]

                if combined_content and len(combined_content.strip()) > 30:
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform=platform,
                        title=title or "Tanpa Judul",
                        text_content=combined_content,
                        status="success",
                        metadata={"description": description}
                    )
                else:
                    return FetchResult(
                        url=url,
                        normalized_url=norm_url,
                        url_hash=url_hash,
                        platform=platform,
                        title=title,
                        status="need_fallback",
                        error_message="Insufficient readable text extracted"
                    )

        except Exception as e:
            logger.warning(f"Public fetcher failed for {norm_url}: {e}")
            return FetchResult(
                url=url,
                normalized_url=norm_url,
                url_hash=url_hash,
                platform=platform,
                status="need_fallback",
                error_message=str(e)
            )
