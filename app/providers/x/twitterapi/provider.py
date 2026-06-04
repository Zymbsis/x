import time
from datetime import datetime
from typing import Annotated, Any

import httpx
from fastapi import Depends

from app.exceptions.base import ProviderError
from app.providers.x.base import ProviderResult, XProvider
from app.providers.x.common import (
    extract_post_id,
    extract_username,
    filter_tweets_by_with_replies,
    in_range,
    limit_reached,
    runtime_exceeded,
    to_unix_timestamp,
)
from app.providers.x.http import get_json_with_retry
from app.providers.x.throttle import RequestGapThrottle
from app.providers.x.twitterapi.client import TwitterApiClientDep, TwitterApiThrottleDep
from app.providers.x.twitterapi.mapper import map_tweet_to_comment, map_tweet_to_post, map_user_to_channel_info
from app.schemas.x.dto import XChannelInfo, XComment, XPost
from app.schemas.x.options import CollectionOptions


class TwitterApiIoProvider(XProvider):
    def __init__(self, client: httpx.AsyncClient, throttle: RequestGapThrottle | None) -> None:
        self._client = client
        self._throttle = throttle

    @staticmethod
    def _validate_twitterapi_payload(data: dict[str, Any]) -> None:
        if data.get("status") == "error":
            message = str(data.get("message") or data.get("msg") or "unknown provider error")
            raise ProviderError(message)

    async def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        return await get_json_with_retry(
            client=self._client,
            path=path,
            params=params,
            throttle=self._throttle,
            validate_payload=self._validate_twitterapi_payload,
        )

    async def get_account_info(self, handles_or_urls: list[str]) -> ProviderResult[XChannelInfo]:
        result: list[XChannelInfo] = []
        raw: list[dict[str, Any]] = []

        for handle_or_url in handles_or_urls:
            try:
                user_name = extract_username(handle_or_url)
                body = await self._get_json("/twitter/user/info", {"userName": user_name})
                raw.append(body)

                payload = body.get("data")
                if not isinstance(payload, dict):
                    raw.append({"handle": handle_or_url, "error": "missing or invalid data payload"})
                    continue

                result.append(map_user_to_channel_info(payload))

            except (ProviderError, ValueError) as exc:
                raw.append({"handle": handle_or_url, "error": str(exc)})

        return ProviderResult[XChannelInfo](data=result, raw=raw)

    async def search_accounts(
        self, query: str, limit: int | None, max_runtime_sec: int | None
    ) -> ProviderResult[XChannelInfo]:
        result: list[XChannelInfo] = []
        raw: list[dict[str, object]] = []

        cursor = ""
        started_at = time.monotonic()

        while True:
            if runtime_exceeded(started_at, max_runtime_sec):
                break

            try:
                body = await self._get_json(
                    "/twitter/user/search",
                    {"query": query, "cursor": cursor},
                )
                raw.append(body)
            except ProviderError as exc:
                raw.append({"query": query, "cursor": cursor, "error": str(exc)})
                break

            users = body.get("users", [])

            if self._map_users_page(users, result, raw, limit):
                return ProviderResult[XChannelInfo](data=result, raw=raw)

            has_next = bool(body.get("has_next_page"))
            next_cursor = str(body.get("next_cursor") or "")
            if not has_next or not next_cursor:
                break

            cursor = next_cursor

        return ProviderResult[XChannelInfo](data=result, raw=raw)

    async def get_account_posts(
        self,
        handle_or_url: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XPost]:
        result: list[XPost] = []
        raw: list[dict[str, object]] = []

        user_name = extract_username(handle_or_url)
        cursor = ""
        started_at = time.monotonic()

        while True:
            if runtime_exceeded(started_at, options.max_runtime_sec):
                break

            try:
                body = await self._get_json(
                    "/twitter/user/last_tweets",
                    {
                        "userName": user_name,
                        "cursor": cursor,
                        "includeReplies": True,
                    },
                )
                raw.append(body)
            except ProviderError as exc:
                raw.append({"handle": handle_or_url, "cursor": cursor, "error": str(exc)})
                break

            payload = body.get("data")
            if not isinstance(payload, dict):
                raw.append({"handle": handle_or_url, "cursor": cursor, "error": "missing or invalid data payload"})
                break

            tweets = filter_tweets_by_with_replies(payload.get("tweets", []), options.with_replies)
            if self._map_posts_page(tweets, result, raw, limit, since, until):
                return ProviderResult[XPost](
                    data=result,
                    raw=raw if options.raw_payloads else [],
                )

            has_next = bool(payload.get("has_next_page"))
            next_cursor = str(payload.get("next_cursor") or "")
            if not has_next or not next_cursor:
                break

            cursor = next_cursor

        return ProviderResult[XPost](
            data=result,
            raw=raw if options.raw_payloads else [],
        )

    async def search_posts(
        self,
        query: str,
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XPost]:
        result: list[XPost] = []
        raw: list[dict[str, object]] = []

        cursor = ""
        started_at = time.monotonic()

        while True:
            if runtime_exceeded(started_at, options.max_runtime_sec):
                break

            try:
                body = await self._get_json(
                    "/twitter/tweet/advanced_search",
                    {"query": query, "cursor": cursor},
                )
                raw.append(body)
            except ProviderError as exc:
                raw.append({"query": query, "cursor": cursor, "error": str(exc)})
                break

            tweets = filter_tweets_by_with_replies(body.get("tweets", []), options.with_replies)
            if self._map_posts_page(tweets, result, raw, limit, since, until):
                return ProviderResult[XPost](
                    data=result,
                    raw=raw if options.raw_payloads else [],
                )

            has_next = bool(body.get("has_next_page"))
            next_cursor = str(body.get("next_cursor") or "")
            if not has_next or not next_cursor:
                break

            cursor = next_cursor

        return ProviderResult[XPost](
            data=result,
            raw=raw if options.raw_payloads else [],
        )

    async def get_posts(self, urls_or_ids: list[str], options: CollectionOptions) -> ProviderResult[XPost]:
        result: list[XPost] = []
        raw: list[dict[str, object]] = []

        tweet_ids: list[str] = []
        for value in urls_or_ids:
            try:
                tweet_ids.append(extract_post_id(value))
            except ValueError as exc:
                raw.append({"url_or_id": value, "error": str(exc)})

        if not tweet_ids:
            return ProviderResult[XPost](data=result, raw=raw if options.raw_payloads else [])

        try:
            body = await self._get_json("/twitter/tweets", {"tweet_ids": ",".join(tweet_ids)})
            raw.append(body)
        except ProviderError as exc:
            raw.append({"tweet_ids": tweet_ids, "error": str(exc)})
            return ProviderResult[XPost](data=result, raw=raw if options.raw_payloads else [])

        tweets = filter_tweets_by_with_replies(body.get("tweets", []), options.with_replies)

        if isinstance(tweets, list):
            for tweet in tweets:
                if not isinstance(tweet, dict):
                    continue
                try:
                    result.append(map_tweet_to_post(tweet))
                except ValueError as exc:
                    raw.append({"tweet_id": tweet.get("id"), "error": str(exc)})

        return ProviderResult[XPost](
            data=result,
            raw=raw if options.raw_payloads else [],
        )

    async def get_replies(
        self,
        post_urls_or_ids: list[str],
        limit: int | None,
        since: datetime | None,
        options: CollectionOptions,
    ) -> ProviderResult[XComment]:
        result: list[XComment] = []
        raw: list[dict[str, object]] = []

        effective_since = options.replies_since or since
        started_at = time.monotonic()

        for post_value in post_urls_or_ids:
            try:
                post_id = extract_post_id(post_value)
            except ValueError as exc:
                raw.append({"post_url_or_id": post_value, "error": str(exc)})
                continue

            cursor = ""

            while True:
                if runtime_exceeded(started_at, options.max_runtime_sec):
                    return ProviderResult[XComment](
                        data=result,
                        raw=raw if options.raw_payloads else [],
                    )

                params: dict[str, Any] = {"tweetId": post_id, "cursor": cursor}
                since_ts = to_unix_timestamp(effective_since)
                if since_ts is not None:
                    params["sinceTime"] = since_ts

                try:
                    body = await self._get_json("/twitter/tweet/replies", params)
                    raw.append(body)
                except ProviderError as exc:
                    raw.append({"post_id": post_id, "cursor": cursor, "error": str(exc)})
                    break

                tweets = filter_tweets_by_with_replies(body.get("tweets", []), options.with_replies)
                if self._map_comments_page(tweets, result, raw, limit, effective_since):
                    return ProviderResult[XComment](
                        data=result,
                        raw=raw if options.raw_payloads else [],
                    )

                has_next = bool(body.get("has_next_page"))
                next_cursor = str(body.get("next_cursor") or "")
                if not has_next or not next_cursor:
                    break

                cursor = next_cursor

        return ProviderResult[XComment](
            data=result,
            raw=raw if options.raw_payloads else [],
        )

    def _map_users_page(
        self,
        users: object,
        result: list[XChannelInfo],
        raw: list[dict[str, Any]],
        limit: int | None,
    ) -> bool:
        if not isinstance(users, list):
            return False

        for user in users:
            if not isinstance(user, dict):
                continue
            try:
                result.append(map_user_to_channel_info(user))
            except ValueError as exc:
                raw.append(
                    {
                        "screen_name": user.get("screen_name") or user.get("userName"),
                        "error": str(exc),
                    }
                )
            if limit_reached(len(result), limit):
                return True

        return False

    def _map_posts_page(
        self,
        tweets: object,
        result: list[XPost],
        raw: list[dict[str, object]],
        limit: int | None,
        since: datetime | None,
        until: datetime | None,
    ) -> bool:
        if not isinstance(tweets, list):
            return False

        for tweet in tweets:
            if not isinstance(tweet, dict):
                continue
            try:
                post = map_tweet_to_post(tweet)
            except ValueError as exc:
                raw.append({"tweet_id": tweet.get("id"), "error": str(exc)})
                continue

            if in_range(post.published_date, since, until):
                result.append(post)

            if limit_reached(len(result), limit):
                return True

        return False

    def _map_comments_page(
        self,
        replies: object,
        result: list[XComment],
        raw: list[dict[str, object]],
        limit: int | None,
        since: datetime | None,
    ) -> bool:
        if not isinstance(replies, list):
            return False

        for tweet in replies:
            if not isinstance(tweet, dict):
                continue
            try:
                comment = map_tweet_to_comment(tweet)
            except ValueError as exc:
                raw.append({"tweet_id": tweet.get("id"), "error": str(exc)})
                continue

            if in_range(comment.time, since, None):
                result.append(comment)

            if limit_reached(len(result), limit):
                return True

        return False


def get_twitterapi_provider(
    client: TwitterApiClientDep,
    throttle: TwitterApiThrottleDep,
) -> TwitterApiIoProvider:
    return TwitterApiIoProvider(client, throttle)


TwitterApiProviderDep = Annotated[TwitterApiIoProvider, Depends(get_twitterapi_provider)]
