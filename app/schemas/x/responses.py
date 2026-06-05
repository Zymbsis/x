from pydantic import BaseModel

from app.schemas.x.dto import ErrorDTO, XChannelInfo, XPost


class BaseResponse[TData](BaseModel):
    data: list[TData]
    errors: list[ErrorDTO]


class AccountResponse(BaseResponse[XChannelInfo]):
    pass


class PostResponse(BaseResponse[XPost]):
    pass


class AccountInfoResponse(AccountResponse):
    pass


class SearchAccountsResponse(AccountResponse):
    pass


class AccountPostsResponse(PostResponse):
    pass


class SearchPostsResponse(PostResponse):
    pass


class PostsResponse(PostResponse):
    pass


class RepliesResponse(PostResponse):
    pass
