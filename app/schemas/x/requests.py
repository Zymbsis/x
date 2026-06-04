from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.x.options import CollectionOptions, ProviderKey


class BaseXRequest(BaseModel):
    provider_key: ProviderKey = ProviderKey.TWITTERAPI_IO
    options: CollectionOptions = CollectionOptions()


class BasePostsQueryRequest(BaseXRequest):
    query: str
    limit: int | None = Field(default=None, ge=1)
    since: datetime | None = None
    until: datetime | None = None


class AccountInfoRequest(BaseModel):
    provider_key: ProviderKey = ProviderKey.TWITTERAPI_IO
    handles_or_urls: list[str]


class SearchAccountsRequest(BaseModel):
    provider_key: ProviderKey = ProviderKey.TWITTERAPI_IO
    query: str
    limit: int | None = Field(default=None, ge=1)
    max_runtime_sec: int | None = Field(default=None, ge=1)


class AccountPostsRequest(BaseXRequest):
    handle_or_url: str
    limit: int | None = Field(default=None, ge=1)
    since: datetime | None = None
    until: datetime | None = None


class SearchPostsRequest(BasePostsQueryRequest):
    pass


class PostsRequest(BaseXRequest):
    urls_or_ids: list[str]


class RepliesRequest(BaseXRequest):
    post_urls_or_ids: list[str]
    limit: int | None = Field(default=None, ge=1)
    since: datetime | None = None
