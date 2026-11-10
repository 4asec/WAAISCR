import pytest
from fetchers.normalizer import URLNormalizer
from fetchers.chain import FetcherChain

def test_url_extraction():
    text = "Cek repo ini deh: https://github.com/torvalds/linux dan artikel https://news.ycombinator.com/item?id=123 keren!"
    urls = URLNormalizer.extract_urls(text)
    assert len(urls) == 2
    assert "https://github.com/torvalds/linux" in urls
    assert "https://news.ycombinator.com/item?id=123" in urls

def test_url_normalization_and_deduplication():
    url1 = "https://example.com/blog/article?utm_source=twitter&utm_medium=social&id=42"
    url2 = "https://example.com/blog/article/?id=42&fbclid=IwAR123"

    norm1 = URLNormalizer.normalize_url(url1)
    norm2 = URLNormalizer.normalize_url(url2)

    # Tracking parameters stripped, host & path normalized
    assert "utm_source" not in norm1
    assert "fbclid" not in norm2
    assert URLNormalizer.hash_url(norm1) == URLNormalizer.hash_url(norm2)

def test_platform_detection():
    assert URLNormalizer.detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert URLNormalizer.detect_platform("https://github.com/octocat/Hello-World") == "github"
    assert URLNormalizer.detect_platform("https://www.reddit.com/r/python") == "reddit"
    assert URLNormalizer.detect_platform("https://techcrunch.com/article") == "web"
