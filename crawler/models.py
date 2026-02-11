from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceDefinition:
    id: str
    name: str
    type: str
    enabled: bool = False
    homepage: str | None = None
    notes: str | None = None
    requires: dict[str, str] | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsItem:
    id: str
    source_id: str
    source_name: str
    title: str
    url: str
    canonical_url: str
    published_at: str
    fetched_at: str
    summary: str | None = None
    keywords: list[str] = field(default_factory=list)
    content_type: str | None = None
    language: str | None = None
    region: str | None = None
