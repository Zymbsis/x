import abc
from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.x.dto import ErrorDTO, XChannelInfo, XPost


@dataclass
class ProviderResult[ItemT]:
    data: list[ItemT]
    errors: list[ErrorDTO] = field(default_factory=list)


class XProvider(abc.ABC):
    @abc.abstractmethod
    async def get_account_info(self, handles_or_urls: list[str]) -> ProviderResult[XChannelInfo]: ...

    @abc.abstractmethod
    async def search_accounts(
        self, query: str, limit: int | None, max_runtime_sec: int
    ) -> ProviderResult[XChannelInfo]: ...

    @abc.abstractmethod
    async def get_account_posts(
        self,
        handle_or_url: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        max_runtime_sec: int,
        with_replies: bool,
    ) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def search_posts(
        self,
        query: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        max_runtime_sec: int,
        with_replies: bool,
    ) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def get_posts(
        self, urls_or_ids: list[str], max_runtime_sec: int, with_replies: bool
    ) -> ProviderResult[XPost]: ...

    @abc.abstractmethod
    async def get_replies(
        self,
        post_urls_or_ids: list[str],
        limit: int | None,
        since: datetime | None,
        max_runtime_sec: int,
    ) -> ProviderResult[XPost]: ...
