from datetime import datetime
from typing import Any

from app.schemas.x.dto import XChannelInfo, XComment, XPost

_DATETIME_FORMATS = (
    "%a %b %d %H:%M:%S %z %Y",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
)


def _parse_datetime(value: str | None) -> datetime:
    if value is None:
        raise ValueError("datetime value is required")

    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    detail = f"Unsupported datetime format: {value}"
    raise ValueError(detail)


def _title_from_text(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    return normalized[:120]


def _canonical_profile_url(user: dict[str, Any]) -> str:
    handle = user.get("userName") or user.get("screen_name") or user.get("username")
    if handle:
        return f"https://x.com/{str(handle).removeprefix('@')}"
    return str(user.get("url") or "")


def map_user_to_channel_info(user: dict[str, Any]) -> XChannelInfo:
    return XChannelInfo(
        channel_name=user.get("name", ""),
        description=user.get("description", ""),
        url=_canonical_profile_url(user),
        subscriber_count=int(user.get("followers") or user.get("followers_count") or 0),
        total_views=None,
        video_count=int(user.get("statusesCount") or user.get("statuses_count") or 0),
        country=user.get("location"),
        channel_logo_url=str(user.get("profilePicture") or user.get("profile_image_url_https") or ""),
        registered_date=_parse_datetime(user.get("createdAt") or user.get("created_at")),
    )


def map_tweet_to_post(tweet: dict[str, Any]) -> XPost:
    text = str(tweet.get("text", "") or "")
    author = tweet.get("author")
    author_name = ""
    author_url = ""

    if isinstance(author, dict):
        author_name = str(author.get("name", "") or "")
        author_url = str(author.get("url", "") or "")

    return XPost(
        title=_title_from_text(text),
        link=str(tweet.get("url", "") or ""),
        published_date=_parse_datetime(tweet.get("createdAt")),
        views=int(tweet["viewCount"]) if tweet.get("viewCount") is not None else None,
        length=None,
        likes=int(tweet.get("likeCount", 0) or 0),
        description=text,
        channel_name=author_name,
        channel_link=author_url,
        comments_count=int(tweet.get("replyCount", 0) or 0),
        thumbnail_url=None,
        category=str(tweet.get("lang", "") or ""),
    )


def map_tweet_to_comment(tweet: dict[str, Any]) -> XComment:
    text = str(tweet.get("text", "") or "")
    author = tweet.get("author")
    author_name = ""

    if isinstance(author, dict):
        author_name = str(author.get("name", "") or "")

    return XComment(
        comment_id=str(tweet.get("id", "") or ""),
        name=author_name,
        comment=text,
        time=_parse_datetime(tweet.get("createdAt")),
        likes=int(tweet.get("likeCount", 0) or 0),
        reply_count=int(tweet["replyCount"]) if tweet.get("replyCount") is not None else None,
    )
