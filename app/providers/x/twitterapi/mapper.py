from typing import Any

from pydantic import AliasChoices, AliasPath, BaseModel, Field

from app.providers.x.common import get_canonical_url, get_snippet_from_text, parse_datetime
from app.schemas.x.dto import XChannelInfo, XPost


class XUserRaw(BaseModel):
    name: str = ""
    user_name: str = Field("", validation_alias=AliasChoices("userName", "screen_name"))
    location: str | None = None
    url: str = ""
    description: str = ""
    followers: int = Field(0, validation_alias=AliasChoices("followers", "followers_count"))
    statuses_count: int = Field(0, validation_alias=AliasChoices("statusesCount", "statuses_count"))
    profile_picture: str = Field("", validation_alias=AliasChoices("profilePicture", "profile_image_url_https"))
    created_at: str = Field("", validation_alias=AliasChoices("createdAt", "created_at"))


def map_user_to_channel_info(user: dict[str, Any]) -> XChannelInfo:
    parsed = XUserRaw.model_validate(user)
    return XChannelInfo(
        channel_name=parsed.name,
        description=parsed.description,
        url=get_canonical_url(parsed.user_name),
        subscriber_count=parsed.followers,
        total_views=None,
        video_count=parsed.statuses_count,
        country=parsed.location,
        channel_logo_url=parsed.profile_picture,
        registered_date=parse_datetime(parsed.created_at),
    )


class XTweetRaw(BaseModel):
    url: str = ""
    text: str = ""
    view_count: int | None = Field(None, validation_alias=AliasChoices("viewCount"))
    like_count: int = Field(0, validation_alias=AliasChoices("likeCount"))
    reply_count: int = Field(0, validation_alias=AliasChoices("replyCount"))
    created_at: str = Field("", validation_alias=AliasChoices("createdAt"))
    lang: str = ""
    author_name: str = Field("", validation_alias=AliasPath("author", "name"))
    author_url: str = Field("", validation_alias=AliasPath("author", "url"))
    thumbnail_url: str | None = Field(
        None, validation_alias=AliasPath("extendedEntities", "media", 0, "media_url_https")
    )
    is_reply: bool = Field(validation_alias=AliasChoices("isReply"))
    reply_to: str | None = Field(None, validation_alias=AliasChoices("inReplyToId"))


def map_tweet_to_post(tweet: dict[str, Any]) -> XPost:
    parsed = XTweetRaw.model_validate(tweet)
    return XPost(
        title=get_snippet_from_text(parsed.text),
        link=parsed.url,
        published_date=parse_datetime(parsed.created_at),
        views=parsed.view_count,
        length=None,
        likes=parsed.like_count,
        description=parsed.text,
        channel_name=parsed.author_name,
        channel_link=parsed.author_url,
        comments_count=parsed.reply_count,
        thumbnail_url=parsed.thumbnail_url,
        category=parsed.lang,
        is_reply=parsed.is_reply,
        reply_to=parsed.reply_to,
    )
