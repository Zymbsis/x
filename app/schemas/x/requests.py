from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.x.options import ProviderKey


class BaseXRequest(BaseModel):
    provider_key: ProviderKey = ProviderKey.TWITTERAPI_IO


class BasePostsRequest(BaseXRequest):
    limit: int | None = Field(default=None, ge=1)
    since: datetime | None = None
    until: datetime | None = None
    max_runtime_sec: int = Field(default=60, ge=1)
    with_replies: bool = True


class AccountInfoRequest(BaseXRequest):
    handles_or_urls: list[str]


class SearchAccountsRequest(BaseXRequest):
    query: str
    limit: int | None = Field(default=None, ge=1)
    max_runtime_sec: int = Field(default=60, ge=1)


class AccountPostsRequest(BasePostsRequest):
    handle_or_url: str


class SearchPostsRequest(BasePostsRequest):
    query: str


class PostsRequest(BaseXRequest):
    urls_or_ids: list[str]
    with_replies: bool = True
    max_runtime_sec: int = Field(default=60, ge=1)


class RepliesRequest(BaseXRequest):
    post_urls_or_ids: list[str]
    limit: int | None = Field(default=None, ge=1)
    since: datetime | None = None
    max_runtime_sec: int = Field(default=60, ge=1)
