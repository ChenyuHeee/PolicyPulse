from __future__ import annotations

import logging
from typing import Any

import httpx
import feedparser

from ..models import SourceDefinition
from ..utils import fetch_text


def fetch_rss(
    source: SourceDefinition,
    user_agent: str,
    timeout: float,
    max_retries: int,
    retry_backoff: float,
) -> list[dict[str, Any]]:
    feed_urls = source.config.get("feed_urls") or []
    if not feed_urls:
        logging.warning("RSS source %s missing feed_urls", source.id)
        return []

    items: list[dict[str, Any]] = []
    headers = {"User-Agent": user_agent}
    with httpx.Client() as client:
        for url in feed_urls:
            content = fetch_text(client, url, headers, timeout, max_retries, retry_backoff)
            parsed = feedparser.parse(content)
            for entry in parsed.entries:
                items.append(
                    {
                        "title": entry.get("title"),
                        "url": entry.get("link") or entry.get("id"),
                        "published_at": entry.get("published") or entry.get("updated"),
                        "summary": entry.get("summary"),
                        "content_type": source.config.get("content_type", "news"),
                        "language": source.config.get("language"),
                        "region": source.config.get("region"),
                    }
                )
    return items
