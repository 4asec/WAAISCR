import hashlib
import re
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# Common tracking parameters to strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "igshid", "si", "feature", "ref", "ref_src"
}

# Regex for detecting URLs in text
URL_REGEX = re.compile(
    r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
    re.IGNORECASE
)

PLATFORM_PATTERNS = [
    ("youtube", re.compile(r'(?:youtube\.com|youtu\.be)', re.IGNORECASE)),
    ("tiktok", re.compile(r'(?:tiktok\.com)', re.IGNORECASE)),
    ("instagram", re.compile(r'(?:instagram\.com)', re.IGNORECASE)),
    ("threads", re.compile(r'(?:threads\.net)', re.IGNORECASE)),
    ("x", re.compile(r'(?:twitter\.com|x\.com)', re.IGNORECASE)),
    ("github", re.compile(r'(?:github\.com)', re.IGNORECASE)),
    ("reddit", re.compile(r'(?:reddit\.com|redd\.it)', re.IGNORECASE)),
    ("linkedin", re.compile(r'(?:linkedin\.com)', re.IGNORECASE)),
]

class URLNormalizer:
    """Normalizes URLs, detects platforms, and computes deduplication hashes."""

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all valid URLs from input text."""
        if not text:
            return []
        matches = URL_REGEX.findall(text)
        return [m.strip(".,;:()[]{}<>\"'") for m in matches]

    @staticmethod
    def detect_platform(url: str) -> str:
        """Identify platform type from URL host."""
        for platform_name, regex in PLATFORM_PATTERNS:
            if regex.search(url):
                return platform_name
        return "web"

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        """Strips tracking parameters and normalizes URL scheme and hostname."""
        parsed = urlparse(raw_url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Remove trailing slash from path if not root
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        # Filter query params
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        cleaned_query = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urlencode(cleaned_query, doseq=True)

        return urlunparse((scheme, netloc, path, parsed.params, new_query, ""))

    @staticmethod
    def hash_url(normalized_url: str) -> str:
        """Generate SHA-256 hash for deduplication checking."""
        return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
