from __future__ import annotations

import re

import httpx

_URL_RE = re.compile(r"^https?://", re.I)


def validate_url(url: str) -> str:
    url = url.strip()
    if not _URL_RE.match(url):
        raise ValueError("URL must start with http:// or https://")
    if len(url) > 2048:
        raise ValueError("URL too long")
    return url


def fetch_article_text(url: str, timeout: float = 15.0) -> str:
    url = validate_url(url)
    headers = {
        "User-Agent": "Legit.ai/1.0 (content verification; +https://github.com)"
    }
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    import trafilatura

    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if not text or len(text.strip()) < 50:
        raise ValueError(
            "Could not extract enough article text from this URL. Try pasting the content directly."
        )
    return text.strip()[:10000]
