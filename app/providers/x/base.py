import abc
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.schemas.x.dto import XChannelInfo, XComment, XPost
from app.schemas.x.options import CollectionOperation, CollectionOptions


@dataclass
class ProviderResult[T]:
    data: list[T]
    raw: list[dict[str, Any]]


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

    @abc.abstractmethod
    async def estimate_cost(
        self, operation: CollectionOperation, expected_items: int, options: CollectionOptions
    ) -> Decimal: ...
