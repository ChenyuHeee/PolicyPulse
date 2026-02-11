from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from dateutil import parser as date_parser


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


TRACKING_PARAMS = {
    "spm",
    "from",
    "ref",
    "ref_src",
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(url: str) -> str:
    if not url:
        return url
    raw = url.strip()
    parsed = urlparse(raw)
    if not parsed.scheme and not parsed.netloc:
        return raw
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = []
    for key, value in query_params:
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_PARAMS:
            continue
        filtered_params.append((key, value))
    query = urlencode(filtered_params, doseq=True)

    return urlunparse((scheme, netloc, path.rstrip("/"), "", query, ""))


def _resolve_timezone(name: str | None) -> timezone | ZoneInfo | None:
    if not name:
        return None
    normalized = name.strip()
    if normalized.upper() in {"UTC", "Z"}:
        return timezone.utc
    try:
        return ZoneInfo(normalized)
    except ZoneInfoNotFoundError:
        logging.warning("Unknown timezone '%s', falling back to UTC", normalized)
        return timezone.utc


def parse_datetime(value: Any, *, default_timezone: str | None = None, fmt: str | None = None) -> str:
    if value is None or value == "":
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if fmt:
            dt = datetime.strptime(text, fmt)
        else:
            dt = date_parser.parse(text)
    if dt.tzinfo is None:
        tzinfo = _resolve_timezone(default_timezone) or timezone.utc
        dt = dt.replace(tzinfo=tzinfo)
    dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def fetch_text(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    timeout: float,
    max_retries: int,
    backoff_sec: float,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            last_error = exc
            logging.warning("Request failed (%s/%s) %s: %s", attempt, max_retries, url, exc)
            if attempt < max_retries:
                time.sleep(backoff_sec * attempt)
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def fetch_json(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    timeout: float,
    max_retries: int,
    backoff_sec: float,
    params: dict[str, Any] | None = None,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            last_error = exc
            logging.warning("Request failed (%s/%s) %s: %s", attempt, max_retries, url, exc)
            if attempt < max_retries:
                time.sleep(backoff_sec * attempt)
    raise RuntimeError(f"Failed to fetch {url}") from last_error
