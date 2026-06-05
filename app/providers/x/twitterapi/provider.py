import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime
from typing import Annotated, Any

import httpx
from aiolimiter import AsyncLimiter
from fastapi import Depends

from app.exceptions.base import ProviderError
from app.providers.x.base import ProviderResult, XProvider
from app.providers.x.common import (
    extract_post_id,
    extract_username,
    filter_tweets_by_date_range,
    filter_tweets_by_with_replies,
    limit_reached,
    runtime_exceeded,
    to_unix_timestamp,
)
from app.providers.x.http import get_json
from app.providers.x.twitterapi.client import TwitterApiClientDep
from app.providers.x.twitterapi.limiter import TwitterApiLimiterDep
from app.providers.x.twitterapi.mapper import map_tweet_to_post, map_user_to_channel_info
from app.schemas.x.dto import ErrorDTO, XChannelInfo, XPost


class TwitterApiIoProvider(XProvider):
    def __init__(self, client: httpx.AsyncClient, limiter: AsyncLimiter) -> None:
        self._client = client
        self._limiter = limiter

    @staticmethod
    def _validate_payload(data: dict[str, Any]) -> None:
        if data.get("status") == "error":
            message = str(data.get("message") or data.get("msg") or "unknown provider error")
            raise ProviderError(message)

    async def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        data = await get_json(
            client=self._client,
            path=path,
            params=params,
            limiter=self._limiter,
        )
        self._validate_payload(data)
        return data

    async def _iter_cursor_pages(
        self,
        fetch: Callable[[str], Awaitable[dict[str, Any]]],
        *,
        max_runtime_sec: int,
        errors: list[ErrorDTO],
        started_at: float | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        timer_start = started_at if started_at is not None else time.monotonic()
        cursor = ""

        while True:
            if runtime_exceeded(timer_start, max_runtime_sec):
                return

            try:
                body = await fetch(cursor)
            except ProviderError as exc:
                if cursor:
                    errors.append(ErrorDTO(source=cursor, detail=str(exc)))
                    return
                raise

            yield body

            has_next = bool(body.get("has_next_page"))
            next_cursor = str(body.get("next_cursor") or "")
            if not has_next or not next_cursor:
                return

            cursor = next_cursor

    async def _get_account_info(self, user_name: str) -> XChannelInfo:
        body = await self._get_json("/twitter/user/info", {"userName": user_name})
        data = body.get("data")
        if message := data.get("message"):
            raise ProviderError(message)
        return map_user_to_channel_info(data)

    async def _search_accounts(self, query: str, cursor: str) -> dict:
        body = await self._get_json("/twitter/user/search", {"query": query, "cursor": cursor})
        if not isinstance(body.get("users"), list):
            raise ProviderError("invalid users payload")
        return body

    async def _get_account_posts(
        self,
        user_name: str,
        cursor: str,
        with_replies: bool,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        body = await self._get_json(
            "/twitter/user/last_tweets",
            {
                "userName": user_name,
                "cursor": cursor,
                "includeReplies": with_replies,
            },
        )
        data = body.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("tweets"), list):
            raise ProviderError("invalid tweets payload")

        return {
            "tweets": filter_tweets_by_date_range(data.get("tweets"), since, until),
            "has_next_page": data.get("has_next_page"),
            "next_cursor": data.get("next_cursor"),
        }

    async def _search_posts(
        self,
        query: str,
        cursor: str,
        with_replies: bool,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, Any]:
        body = await self._get_json(
            "/twitter/tweet/advanced_search",
            {"query": query, "cursor": cursor},
        )
        if not isinstance(body.get("tweets"), list):
            raise ProviderError("invalid tweets payload")
        tweets = filter_tweets_by_with_replies(body["tweets"], with_replies)
        tweets = filter_tweets_by_date_range(tweets, since, until)

        return {**body, "tweets": tweets}

    async def _get_posts(self, tweet_ids: str, with_replies: bool) -> dict[str, Any]:
        body = await self._get_json("/twitter/tweets", {"tweet_ids": tweet_ids})
        if not isinstance(body.get("tweets"), list):
            raise ProviderError("invalid tweets payload")

        tweets = filter_tweets_by_with_replies(body["tweets"], with_replies)
        return {**body, "tweets": tweets}

    async def _get_replies(self, post_id: str, cursor: str, since: datetime | None) -> dict[str, Any]:
        params: dict[str, Any] = {"tweetId": post_id, "cursor": cursor}
        since_ts = to_unix_timestamp(since)
        if since_ts is not None:
            params["sinceTime"] = since_ts

        body = await self._get_json("/twitter/tweet/replies", params)
        if not isinstance(body.get("tweets"), list):
            raise ProviderError("invalid tweets payload")

        tweets = [t for t in body["tweets"] if str(t.get("id")) != post_id]

        return {
            "tweets": tweets,
            "has_next_page": body.get("has_next_page"),
            "next_cursor": body.get("next_cursor"),
        }

    async def get_account_info(self, handles_or_urls: list[str]) -> ProviderResult[XChannelInfo]:
        data: list[XChannelInfo] = []
        errors: list[ErrorDTO] = []

        outcomes = await asyncio.gather(
            *[self._get_account_info(extract_username(h)) for h in handles_or_urls],
            return_exceptions=True,
        )
        for handle_or_url, outcome in zip(handles_or_urls, outcomes):
            if isinstance(outcome, BaseException):
                errors.append(ErrorDTO(source=handle_or_url, detail=str(outcome)))
            else:
                data.append(outcome)

        return ProviderResult[XChannelInfo](data=data, errors=errors)

    async def search_accounts(
        self, query: str, limit: int | None, max_runtime_sec: int
    ) -> ProviderResult[XChannelInfo]:
        data: list[XChannelInfo] = []
        errors: list[ErrorDTO] = []

        async for body in self._iter_cursor_pages(
            fetch=lambda cursor: self._search_accounts(query, cursor), max_runtime_sec=max_runtime_sec, errors=errors
        ):
            for user in body["users"]:
                data.append(map_user_to_channel_info(user))
                if limit_reached(len(data), limit):
                    return ProviderResult[XChannelInfo](data=data, errors=errors)

        return ProviderResult[XChannelInfo](data=data, errors=errors)

    async def get_account_posts(
        self,
        handle_or_url: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        max_runtime_sec: int,
        with_replies: bool,
    ) -> ProviderResult[XPost]:
        data: list[XPost] = []
        errors: list[ErrorDTO] = []
        user_name = extract_username(handle_or_url)

        async for body in self._iter_cursor_pages(
            fetch=lambda cursor: self._get_account_posts(user_name, cursor, with_replies, since, until),
            max_runtime_sec=max_runtime_sec,
            errors=errors,
        ):
            for tweet in body["tweets"]:
                data.append(map_tweet_to_post(tweet))
                if limit_reached(len(data), limit):
                    return ProviderResult[XPost](data=data, errors=errors)

        return ProviderResult[XPost](data=data, errors=errors)

    async def search_posts(
        self,
        query: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        max_runtime_sec: int,
        with_replies: bool,
    ) -> ProviderResult[XPost]:
        data: list[XPost] = []
        errors: list[ErrorDTO] = []

        async for body in self._iter_cursor_pages(
            fetch=lambda cursor: self._search_posts(query, cursor, with_replies, since, until),
            max_runtime_sec=max_runtime_sec,
            errors=errors,
        ):
            for tweet in body["tweets"]:
                data.append(map_tweet_to_post(tweet))
                if limit_reached(len(data), limit):
                    return ProviderResult[XPost](data=data, errors=errors)

        return ProviderResult[XPost](data=data, errors=errors)

    async def get_posts(
        self,
        urls_or_ids: list[str],
        _max_runtime_sec: int,
        with_replies: bool,
    ) -> ProviderResult[XPost]:
        data: list[XPost] = []
        errors: list[ErrorDTO] = []
        sources: list[str] = []
        tweet_ids: list[str] = []

        for url in urls_or_ids:
            try:
                sources.append(url)
                tweet_ids.append(extract_post_id(url))
            except ValueError as exc:
                errors.append(ErrorDTO(source=url, detail=str(exc)))

        if not tweet_ids:
            return ProviderResult[XPost](data=data, errors=errors)

        body = await self._get_posts(",".join(tweet_ids), with_replies)
        returned_ids = {str(tweet["id"]) for tweet in body["tweets"]}

        for source, tweet_id in zip(sources, tweet_ids, strict=True):
            if tweet_id not in returned_ids:
                errors.append(ErrorDTO(source=source, detail="tweet not found"))

        data = [map_tweet_to_post(tweet) for tweet in body["tweets"]]

        return ProviderResult[XPost](data=data, errors=errors)

    async def get_replies(
        self,
        post_urls_or_ids: list[str],
        limit: int | None,
        since: datetime | None,
        max_runtime_sec: int,
    ) -> ProviderResult[XPost]:
        data: list[XPost] = []
        errors: list[ErrorDTO] = []
        sources: list[str] = []
        post_ids: list[str] = []

        for url in post_urls_or_ids:
            try:
                sources.append(url)
                post_ids.append(extract_post_id(url))
            except ValueError as exc:
                errors.append(ErrorDTO(source=url, detail=str(exc)))

        started_at = time.monotonic()

        for source, post_id in zip(sources, post_ids, strict=True):
            if runtime_exceeded(started_at, max_runtime_sec):
                break

            count_before = len(data)
            had_page = False

            try:
                async for body in self._iter_cursor_pages(
                    fetch=lambda cursor, pid=post_id: self._get_replies(pid, cursor, since),
                    max_runtime_sec=max_runtime_sec,
                    errors=errors,
                    started_at=started_at,
                ):
                    had_page = True
                    for tweet in body["tweets"]:
                        data.append(map_tweet_to_post(tweet))
                        if limit_reached(len(data), limit):
                            return ProviderResult(data=data, errors=errors)
            except ProviderError as exc:
                errors.append(ErrorDTO(source=source, detail=str(exc)))
                continue

            if had_page and len(data) == count_before:
                errors.append(ErrorDTO(source=source, detail="no replies found"))

        return ProviderResult(data=data, errors=errors)


def get_twitterapi_provider(client: TwitterApiClientDep, limiter: TwitterApiLimiterDep) -> TwitterApiIoProvider:
    return TwitterApiIoProvider(client, limiter)


TwitterApiProviderDep = Annotated[TwitterApiIoProvider, Depends(get_twitterapi_provider)]
