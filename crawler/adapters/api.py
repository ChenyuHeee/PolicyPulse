from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urljoin

import httpx

from ..models import SourceDefinition
from ..utils import fetch_json


def _extract_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def fetch_api(
    source: SourceDefinition,
    user_agent: str,
    timeout: float,
    max_retries: int,
    retry_backoff: float,
) -> list[dict[str, Any]]:
    endpoint = source.config.get("endpoint")
    if not endpoint:
        logging.warning("API source %s missing endpoint", source.id)
        return []

    headers = {"User-Agent": user_agent}
    params = source.config.get("params") or {}
    auth_env = source.config.get("auth_env") or {}
    resolved_params = dict(params)
    for param_key, env_key in auth_env.items():
        env_value = os.getenv(env_key)
        if env_value:
            resolved_params[param_key] = env_value
    items_path = source.config.get("items_path")
    field_map = source.config.get("field_map") or {}
    base_url = source.config.get("base_url")
    url_template = source.config.get("url_template")
    title_template = source.config.get("title_template")
    summary_template = source.config.get("summary_template")
    published_at_template = source.config.get("published_at_template")
    static_fields = source.config.get("static_fields") or {}

    with httpx.Client() as client:
        payload = fetch_json(
            client,
            endpoint,
            headers,
            timeout,
            max_retries,
            retry_backoff,
            params=resolved_params,
        )

    raw_items = _extract_path(payload, items_path) if items_path else payload
    if not isinstance(raw_items, list):
        logging.warning("API source %s returned unexpected payload", source.id)
        return []

    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        merged = dict(raw)
        for key, value in static_fields.items():
            merged.setdefault(key, value)

        title = merged.get(field_map.get("title", "title"))
        if not title and title_template:
            try:
                title = title_template.format_map(merged)
            except KeyError:
                title = None

        url = merged.get(field_map.get("url", "url"))
        if not url and url_template:
            try:
                url = url_template.format_map(merged)
            except KeyError:
                url = None
        if url and base_url:
            url = urljoin(base_url, str(url))

        published_at = merged.get(field_map.get("published_at", "published_at"))
        if not published_at and published_at_template:
            try:
                published_at = published_at_template.format_map(merged)
            except KeyError:
                published_at = None

        summary = merged.get(field_map.get("summary", "summary"))
        if not summary and summary_template:
            try:
                summary = summary_template.format_map(merged)
            except KeyError:
                summary = None

        items.append(
            {
                "title": title,
                "url": url,
                "published_at": published_at,
                "summary": summary,
                "content_type": source.config.get("content_type", "news"),
                "language": source.config.get("language"),
                "region": source.config.get("region"),
            }
        )
    return items
