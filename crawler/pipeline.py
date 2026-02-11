from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .adapters.api import fetch_api
from .adapters.html import fetch_html
from .adapters.rss import fetch_rss
from .config import load_settings, load_sources
from .storage import load_index, load_news_items, write_index, write_news_items
from .utils import canonicalize_url, parse_datetime, sha256_text


ADAPTERS = {
    "rss": fetch_rss,
    "html": fetch_html,
    "api": fetch_api,
}


def _normalize_item(raw: dict[str, Any], source: Any) -> dict[str, Any]:
    source_id = source.id
    source_name = source.name
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()
    canonical_url = canonicalize_url(url)
    fetched_at = parse_datetime(None)
    try:
        published_format = source.config.get("published_format")
        published_timezone = source.config.get("published_timezone")
        if not published_timezone and source.config.get("region") == "CN":
            published_timezone = "Asia/Shanghai"
        published_at = parse_datetime(
            raw.get("published_at"),
            default_timezone=published_timezone,
            fmt=published_format,
        )
    except Exception:
        published_at = fetched_at

    item_id = sha256_text(f"{source_id}:{canonical_url}")

    return {
        "id": item_id,
        "source_id": source_id,
        "source_name": source_name,
        "title": title,
        "url": url,
        "canonical_url": canonical_url,
        "published_at": published_at,
        "fetched_at": fetched_at,
        "summary": raw.get("summary"),
        "keywords": raw.get("keywords") or [],
        "content_type": raw.get("content_type"),
        "language": raw.get("language"),
        "region": raw.get("region"),
    }


def crawl(data_path: str, index_path: str) -> None:
    settings = load_settings()
    sources = load_sources()

    data_file = Path(data_path)
    index_file = Path(index_path)

    existing_items = load_news_items(data_file)
    existing_ids = {item.get("id") for item in existing_items if item.get("id")}
    previous_index = load_index(index_file)
    previous_state = previous_index.get("state", {}).get("sources", {})

    max_retries = int(settings.get("max_retries", 3))
    retry_backoff = float(settings.get("retry_backoff_sec", 2))
    timeout = float(settings.get("request_timeout_sec", 20))
    crawl_delay = float(settings.get("crawl_delay_sec", 1.0))
    user_agent = settings.get("user_agent", "PolicyPulseBot/0.1")
    retention = settings.get("retention", {})

    new_items: list[dict[str, Any]] = []
    source_stats: dict[str, dict[str, Any]] = {}
    state_sources: dict[str, dict[str, Any]] = {**previous_state}

    alerting = settings.get("alerting", {})
    alerting_enabled = alerting.get("enabled", True)
    failure_threshold = int(alerting.get("failure_streak_threshold", 3))
    zero_new_threshold = int(alerting.get("zero_new_streak_threshold", 3))

    for source in sources:
        if not source.enabled:
            logging.info("Skip %s (disabled)", source.id)
            continue

        missing_env = []
        if source.requires:
            for env_key in source.requires:
                if not os.getenv(env_key):
                    missing_env.append(env_key)
        if missing_env:
            logging.warning("Skip %s (missing env: %s)", source.id, ", ".join(missing_env))
            previous = previous_state.get(source.id, {})
            state_sources[source.id] = {
                "failure_streak": int(previous.get("failure_streak", 0)),
                "zero_new_streak": int(previous.get("zero_new_streak", 0)),
                "last_status": "skipped",
                "last_error": f"Missing env: {', '.join(missing_env)}",
                "last_run": parse_datetime(None),
            }
            source_stats[source.id] = {
                "fetched": 0,
                "new": 0,
                "skipped": 0,
                "status": "skipped",
                "reason": "missing env",
                "failure_streak": state_sources[source.id]["failure_streak"],
                "zero_new_streak": state_sources[source.id]["zero_new_streak"],
                "last_run": state_sources[source.id]["last_run"],
                "last_error": state_sources[source.id].get("last_error"),
            }
            continue

        adapter = ADAPTERS.get(source.type)
        if adapter is None:
            logging.warning("Skip %s (unknown adapter: %s)", source.id, source.type)
            previous = previous_state.get(source.id, {})
            state_sources[source.id] = {
                "failure_streak": int(previous.get("failure_streak", 0)),
                "zero_new_streak": int(previous.get("zero_new_streak", 0)),
                "last_status": "skipped",
                "last_error": "Unknown adapter",
                "last_run": parse_datetime(None),
            }
            source_stats[source.id] = {
                "fetched": 0,
                "new": 0,
                "skipped": 0,
                "status": "skipped",
                "reason": "unknown adapter",
                "failure_streak": state_sources[source.id]["failure_streak"],
                "zero_new_streak": state_sources[source.id]["zero_new_streak"],
                "last_run": state_sources[source.id]["last_run"],
                "last_error": state_sources[source.id].get("last_error"),
            }
            continue

        effective_user_agent = user_agent
        if source.requires:
            for env_key in source.requires:
                if env_key.endswith("USER_AGENT") and os.getenv(env_key):
                    effective_user_agent = os.getenv(env_key)

        try:
            raw_items = adapter(
                source=source,
                user_agent=effective_user_agent,
                timeout=timeout,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
            )
        except Exception as exc:
            logging.exception("Source %s failed: %s", source.id, exc)
            previous = previous_state.get(source.id, {})
            failure_streak = int(previous.get("failure_streak", 0)) + 1
            zero_new_streak = int(previous.get("zero_new_streak", 0))
            state_sources[source.id] = {
                "failure_streak": failure_streak,
                "zero_new_streak": zero_new_streak,
                "last_status": "failed",
                "last_error": str(exc),
                "last_run": parse_datetime(None),
            }
            source_stats[source.id] = {
                "fetched": 0,
                "new": 0,
                "skipped": 0,
                "status": "failed",
                "failure_streak": state_sources[source.id]["failure_streak"],
                "zero_new_streak": state_sources[source.id]["zero_new_streak"],
                "last_run": state_sources[source.id]["last_run"],
                "last_error": state_sources[source.id].get("last_error"),
            }
            continue

        fetched_count = len(raw_items)
        added = 0
        skipped = 0
        for raw in raw_items:
            normalized = _normalize_item(raw, source)
            if not normalized["title"] or not normalized["url"]:
                skipped += 1
                continue
            if normalized["id"] in existing_ids:
                skipped += 1
                continue
            existing_ids.add(normalized["id"])
            new_items.append(normalized)
            added += 1

        logging.info(
            "Source %s fetched=%s new=%s skipped=%s",
            source.id,
            fetched_count,
            added,
            skipped,
        )

        previous = previous_state.get(source.id, {})
        failure_streak = 0
        if added == 0:
            zero_new_streak = int(previous.get("zero_new_streak", 0)) + 1
        else:
            zero_new_streak = 0
        state_sources[source.id] = {
            "failure_streak": failure_streak,
            "zero_new_streak": zero_new_streak,
            "last_status": "success",
            "last_error": None,
            "last_run": parse_datetime(None),
        }

        source_stats[source.id] = {
            "fetched": fetched_count,
            "new": added,
            "skipped": skipped,
            "status": "success",
            "failure_streak": state_sources[source.id]["failure_streak"],
            "zero_new_streak": state_sources[source.id]["zero_new_streak"],
            "last_run": state_sources[source.id]["last_run"],
            "last_error": state_sources[source.id].get("last_error"),
        }

        if crawl_delay > 0:
            from time import sleep

            sleep(crawl_delay)

    combined = existing_items + new_items
    combined.sort(key=lambda item: item.get("published_at", ""), reverse=True)

    if retention.get("enabled"):
        max_items = retention.get("max_items")
        if isinstance(max_items, int) and max_items > 0:
            combined = combined[:max_items]

        days = retention.get("days")
        if isinstance(days, int) and days > 0:
            from datetime import datetime, timedelta, timezone

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            combined = [
                item
                for item in combined
                if item.get("published_at")
                and item["published_at"] >= cutoff.isoformat()
            ]

    alerts: list[dict[str, Any]] = []
    if alerting_enabled:
        for source_id, state in state_sources.items():
            if failure_threshold > 0 and state.get("failure_streak", 0) >= failure_threshold:
                alerts.append(
                    {
                        "source_id": source_id,
                        "type": "failure_streak",
                        "streak": state.get("failure_streak", 0),
                        "message": "Consecutive failures detected. Check selectors or endpoint.",
                        "last_error": state.get("last_error"),
                        "last_run": state.get("last_run"),
                    }
                )
            if zero_new_threshold > 0 and state.get("zero_new_streak", 0) >= zero_new_threshold:
                alerts.append(
                    {
                        "source_id": source_id,
                        "type": "zero_new_streak",
                        "streak": state.get("zero_new_streak", 0),
                        "message": "No new items in consecutive runs. Check selectors or endpoint.",
                        "last_run": state.get("last_run"),
                    }
                )

    write_news_items(data_file, combined)
    write_index(
        index_file,
        combined,
        source_stats=source_stats,
        state={"sources": state_sources},
        alerts=alerts,
    )

    logging.info("Total items=%s (new=%s)", len(combined), len(new_items))
