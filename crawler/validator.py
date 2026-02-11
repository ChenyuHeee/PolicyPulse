from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .utils import parse_datetime

REQUIRED_FIELDS = ["id", "source_id", "source_name", "title", "url", "published_at"]


def validate(data_path: str) -> None:
    file_path = Path(data_path)
    if not file_path.exists():
        raise SystemExit("data file not found")

    ids: set[str] = set()
    errors: list[str] = []

    with file_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                errors.append(f"Line {line_no}: invalid json")
                continue

            for field in REQUIRED_FIELDS:
                if not item.get(field):
                    errors.append(f"Line {line_no}: missing {field}")

            item_id = item.get("id")
            if item_id:
                if item_id in ids:
                    errors.append(f"Line {line_no}: duplicate id {item_id}")
                ids.add(item_id)

            try:
                datetime.fromisoformat(parse_datetime(item.get("published_at")))
            except ValueError:
                errors.append(f"Line {line_no}: invalid published_at")

    if errors:
        raise SystemExit("\n".join(errors))
