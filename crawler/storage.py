from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .utils import parse_datetime


def load_news_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            try:
                items.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return items


def load_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def write_news_items(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_index(
    path: Path,
    items: list[dict[str, Any]],
    *,
    source_stats: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    alerts: list[dict[str, Any]] | None = None,
) -> None:
    sources: dict[str, int] = {}
    for item in items:
        source_id = item.get("source_id")
        if not source_id:
            continue
        sources[source_id] = sources.get(source_id, 0) + 1

    payload = {
        "generated_at": parse_datetime(None),
        "total": len(items),
        "sources": sources,
    }
    if source_stats is not None:
        payload["last_run"] = {
            "completed_at": parse_datetime(None),
            "sources": source_stats,
        }
    if state is not None:
        payload["state"] = state
    if alerts is not None:
        payload["alerts"] = alerts
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
