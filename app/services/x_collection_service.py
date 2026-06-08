from typing import Annotated

from fastapi import Depends

from app.providers.x.base import ProviderResult, XProvider
from app.providers.x.registry import XProviderDep
from app.schemas.x.dto import XChannelInfo, XComment, XPost
from app.schemas.x.requests import (
    AccountInfoRequest,
    AccountPostsRequest,
    PostsRequest,
    RepliesRequest,
    SearchAccountsRequest,
    SearchPostsRequest,
)


class XCollectionService:
    def __init__(self, provider: XProvider) -> None:
        self._provider = provider

    async def get_account_info(self, payload: AccountInfoRequest) -> ProviderResult[XChannelInfo]:
        return await self._provider.get_account_info(payload.handles_or_urls)

    async def search_accounts(self, payload: SearchAccountsRequest) -> ProviderResult[XChannelInfo]:
        return await self._provider.search_accounts(payload.query, payload.limit, payload.max_runtime_sec)

    async def get_account_posts(self, payload: AccountPostsRequest) -> ProviderResult[XPost]:
        return await self._provider.get_account_posts(
            payload.handle_or_url,
            payload.limit,
            payload.since,
            payload.until,
            payload.options,
        )

    async def search_posts(self, payload: SearchPostsRequest) -> ProviderResult[XPost]:
        return await self._provider.search_posts(
            payload.query,
            payload.limit,
            payload.since,
            payload.until,
            payload.options,
        )

    async def get_posts(self, payload: PostsRequest) -> ProviderResult[XPost]:
        return await self._provider.get_posts(payload.urls_or_ids, payload.options)

    async def get_replies(self, payload: RepliesRequest) -> ProviderResult[XComment]:
        return await self._provider.get_replies(
            payload.post_urls_or_ids,
            payload.limit,
            payload.since,
            payload.options,
        )


def get_x_collection_service(provider: XProviderDep) -> XCollectionService:
    return XCollectionService(provider)


XCollectionServiceDep = Annotated[XCollectionService, Depends(get_x_collection_service)]
