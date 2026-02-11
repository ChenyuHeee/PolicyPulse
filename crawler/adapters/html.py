from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..models import SourceDefinition
from ..utils import fetch_text


def fetch_html(
    source: SourceDefinition,
    user_agent: str,
    timeout: float,
    max_retries: int,
    retry_backoff: float,
) -> list[dict[str, Any]]:
    list_urls = source.config.get("list_urls") or []
    item_selector = source.config.get("item_selector")
    title_selector = source.config.get("title_selector")
    url_selector = source.config.get("url_selector")
    published_selector = source.config.get("published_selector")

    if not list_urls or not item_selector or not title_selector or not url_selector:
        logging.warning("HTML source %s missing selector config", source.id)
        return []

    headers = {"User-Agent": user_agent}

    items: list[dict[str, Any]] = []
    with httpx.Client() as client:
        for url in list_urls:
            html = fetch_text(client, url, headers, timeout, max_retries, retry_backoff)
            soup = BeautifulSoup(html, "lxml")
            for row in soup.select(item_selector):
                title_el = row.select_one(title_selector)
                url_el = row.select_one(url_selector)
                if not title_el or not url_el:
                    continue
                base_url = source.config.get("base_url") or url
                raw_url = url_el.get("href")
                absolute_url = urljoin(base_url, raw_url) if raw_url else None
                items.append(
                    {
                        "title": title_el.get_text(strip=True),
                        "url": absolute_url,
                        "published_at": row.select_one(published_selector).get_text(strip=True)
                        if published_selector
                        else None,
                        "summary": None,
                        "content_type": source.config.get("content_type", "news"),
                        "language": source.config.get("language"),
                        "region": source.config.get("region"),
                    }
                )
    return items
