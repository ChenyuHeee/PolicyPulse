from __future__ import annotations

import logging
import os
from typing import Any

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
        items.append(
            {
                "title": raw.get(field_map.get("title", "title")),
                "url": raw.get(field_map.get("url", "url")),
                "published_at": raw.get(field_map.get("published_at", "published_at")),
                "summary": raw.get(field_map.get("summary", "summary")),
                "content_type": source.config.get("content_type", "news"),
                "language": source.config.get("language"),
                "region": source.config.get("region"),
            }
        )
    return items
