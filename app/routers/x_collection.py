from fastapi import APIRouter, Depends

from app.schemas.x.requests import (
    AccountInfoRequest,
    AccountPostsRequest,
    PostsRequest,
    RepliesRequest,
    SearchAccountsRequest,
    SearchPostsRequest,
)
from app.schemas.x.responses import (
    AccountInfoResponse,
    AccountPostsResponse,
    PostsResponse,
    RepliesResponse,
    SearchAccountsResponse,
    SearchPostsResponse,
)
from app.security.security import verify_api_key
from app.services.x_collection_service import XCollectionServiceDep

router = APIRouter(prefix="/x", tags=["x-collection"], dependencies=[Depends(verify_api_key)])


@router.post("/accounts/info", response_model=AccountInfoResponse)
async def get_account_info(payload: AccountInfoRequest, service: XCollectionServiceDep) -> AccountInfoResponse:
    result = await service.get_account_info(payload)
    return AccountInfoResponse(data=result.data, raw=result.raw)


@router.post("/accounts/search", response_model=SearchAccountsResponse)
async def search_accounts(payload: SearchAccountsRequest, service: XCollectionServiceDep) -> SearchAccountsResponse:
    result = await service.search_accounts(payload)
    return SearchAccountsResponse(data=result.data, raw=result.raw)


@router.post("/accounts/posts", response_model=AccountPostsResponse)
async def get_account_posts(payload: AccountPostsRequest, service: XCollectionServiceDep) -> AccountPostsResponse:
    result = await service.get_account_posts(payload)
    return AccountPostsResponse(data=result.data, raw=result.raw)


@router.post("/posts/search", response_model=SearchPostsResponse)
async def search_posts(payload: SearchPostsRequest, service: XCollectionServiceDep) -> SearchPostsResponse:
    result = await service.search_posts(payload)
    return SearchPostsResponse(data=result.data, raw=result.raw)


@router.post("/posts/get", response_model=PostsResponse)
async def get_posts(payload: PostsRequest, service: XCollectionServiceDep) -> PostsResponse:
    result = await service.get_posts(payload)
    return PostsResponse(data=result.data, raw=result.raw)


@router.post("/posts/replies", response_model=RepliesResponse)
async def get_replies(payload: RepliesRequest, service: XCollectionServiceDep) -> RepliesResponse:
    result = await service.get_replies(payload)
    return RepliesResponse(data=result.data, raw=result.raw)
