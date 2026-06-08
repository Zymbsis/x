from typing import Any

from pydantic import BaseModel, ValidationError

from app.exceptions.base import ProviderError
from app.providers.x.twitterapi.mapper import XUserRaw


class UserInfoData(XUserRaw):
    message: str | None = None


class UserInfoResponse(BaseModel):
    data: UserInfoData


class CursorPage(BaseModel):
    has_next_page: bool = False
    next_cursor: str = ""


class SearchAccountsPage(CursorPage):
    users: list[dict[str, Any]]


class LastTweetsData(CursorPage):
    tweets: list[dict[str, Any]]


class LastTweetsResponse(BaseModel):
    data: LastTweetsData


class TweetsPage(CursorPage):
    tweets: list[dict[str, Any]]


def parse_response[T: BaseModel](model: type[T], data: dict[str, Any]) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ProviderError(str(exc)) from exc
