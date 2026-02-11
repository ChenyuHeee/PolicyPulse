from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from .models import SourceDefinition
from .sources.registry import SOURCES

CONFIG_PATH = Path(__file__).resolve().parent / "sources_config.yaml"


def load_config() -> tuple[dict[str, Any], dict[str, Any]]:
    if not CONFIG_PATH.exists():
        return {}, {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    settings = raw.get("settings", {})
    overrides = raw.get("sources", {})
    return settings, overrides


def load_sources() -> list[SourceDefinition]:
    _, overrides = load_config()
    merged: list[SourceDefinition] = []
    for source in SOURCES:
        override = overrides.get(source.id, {})
        enabled = override.get("enabled", source.enabled)
        config = {**source.config, **override.get("config", {})}
        merged.append(
            replace(
                source,
                enabled=enabled,
                config=config,
                notes=override.get("notes", source.notes),
            )
        )
    return merged


def load_settings() -> dict[str, Any]:
    settings, _ = load_config()
    return settings
