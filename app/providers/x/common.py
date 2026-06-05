import re
import time
from datetime import datetime
from typing import Any

STATUS_URL_RE = re.compile(r"/status/(\d+)")
_DATETIME_FORMATS = (
    "%a %b %d %H:%M:%S %z %Y",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
)


def extract_username(handle_or_url: str) -> str:
    value = handle_or_url.strip()
    if value.startswith(("http://", "https://")):
        value = value.rstrip("/").split("/")[-1]
    return value.removeprefix("@")


def extract_post_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if value.isdigit():
        return value
    match = STATUS_URL_RE.search(value)
    if match:
        return match.group(1)
    detail = f"Cannot extract post ID from: {url_or_id!r}"
    raise ValueError(detail)


def parse_datetime(value: str | None) -> datetime:
    if value is None:
        raise ValueError("datetime value is required")

    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    detail = f"Unsupported datetime format: {value}"
    raise ValueError(detail)


def get_canonical_url(handle: str) -> str:
    return f"https://x.com/{handle}"


def get_snippet_from_text(text: str) -> str:
    return (" ".join(text.split()))[:120]


def in_range(moment: datetime, since: datetime | None, until: datetime | None) -> bool:
    return (since is None or moment >= since) and (until is None or moment <= until)


def runtime_exceeded(started_at: float, max_runtime_sec: int | None) -> bool:
    return max_runtime_sec is not None and (time.monotonic() - started_at) >= max_runtime_sec


def limit_reached(collected_count: int, limit: int | None) -> bool:
    return limit is not None and collected_count >= limit


def to_unix_timestamp(value: datetime | None) -> int | None:
    return None if value is None else int(value.timestamp())


def filter_tweets_by_date_range(
    tweets: list[dict[str, Any]],
    since: datetime | None,
    until: datetime | None,
) -> list[dict]:
    if since is None and until is None:
        return tweets

    return [
        tweet
        for tweet in tweets
        if tweet.get("createdAt") and in_range(parse_datetime(tweet["createdAt"]), since, until)
    ]


def filter_tweets_by_with_replies(
    tweets: list[dict[str, Any]],
    with_replies: bool,
) -> list[dict[str, Any]]:
    if with_replies:
        return tweets

    return [tweet for tweet in tweets if not tweet.get("isReply")]
