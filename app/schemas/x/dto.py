from datetime import datetime

from pydantic import BaseModel


class XChannelInfo(BaseModel):
    channel_name: str
    description: str
    url: str
    subscriber_count: int
    total_views: int | None
    video_count: int
    country: str | None
    channel_logo_url: str
    registered_date: datetime


class XPost(BaseModel):
    title: str
    link: str
    published_date: datetime
    views: int | None
    length: int | None
    likes: int
    description: str
    channel_name: str
    channel_link: str
    comments_count: int
    thumbnail_url: str | None
    category: str


class XComment(BaseModel):
    comment_id: str
    name: str
    comment: str
    time: datetime
    likes: int
    reply_count: int | None
