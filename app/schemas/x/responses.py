from pydantic import BaseModel

from app.schemas.x.dto import XChannelInfo, XComment, XPost


class AccountInfoResponse(BaseModel):
    data: list[XChannelInfo]
    raw: list[dict]


class SearchAccountsResponse(BaseModel):
    data: list[XChannelInfo]
    raw: list[dict]


class AccountPostsResponse(BaseModel):
    data: list[XPost]
    raw: list[dict]


class SearchPostsResponse(BaseModel):
    data: list[XPost]
    raw: list[dict]


class PostsResponse(BaseModel):
    data: list[XPost]
    raw: list[dict]


class RepliesResponse(BaseModel):
    data: list[XComment]
    raw: list[dict]
