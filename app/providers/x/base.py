import abc
from dataclasses import dataclass
from datetime import datetime

from app.schemas.x.dto import XChannelInfo, XComment, XPost
from app.schemas.x.options import CollectionOptions


@dataclass
class ProviderResult[ItemT]:
    data: list[ItemT]
    raw: list[dict[str, object]]


class XProvider(abc.ABC):
    @abc.abstractmethod
    async def get_account_info(self, handles_or_urls: list[str]) -> ProviderResult[XChannelInfo]: ...

    @abc.abstractmethod
    async def search_accounts(
        self, query: str, limit: int | None, max_runtime_sec: int | None
    ) -> ProviderResult[XChannelInfo]: ...

    @abc.abstractmethod
    async def get_account_posts(
        self,
        handle_or_url: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def search_posts(
        self,
        query: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def get_posts(self, urls_or_ids: list[str], options: CollectionOptions) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def get_replies(
        self,
        post_urls_or_ids: list[str],
        limit: int | None,
        since: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XComment]: ...
