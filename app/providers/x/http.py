import asyncio
from collections.abc import Callable
from typing import Any

import httpx

from app.exceptions.base import ProviderError
from app.providers.x.throttle import RequestGapThrottle

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable_http_error(exc: httpx.HTTPError) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code if exc.response is not None else None
        return status in RETRYABLE_STATUS_CODES
    return False


async def get_json_with_retry(
    *,
    client: httpx.AsyncClient,
    path: str,
    params: dict[str, Any],
    throttle: RequestGapThrottle | None,
    validate_payload: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    for attempt in (1, 2):
        if throttle is not None:
            await throttle.wait_turn()

        try:
            response = await client.get(path, params=params)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ProviderError("response is not a JSON object")
            validate_payload(data)

        except httpx.HTTPError as exc:
            if attempt == 1 and _is_retryable_http_error(exc):
                await asyncio.sleep(0.7)
                continue
            detail = f"request failed: {exc}"
            raise ProviderError(detail) from exc

        except ValueError as exc:
            detail = f"request failed: {exc}"
            raise ProviderError(detail) from exc
        else:
            return data
        finally:
            if throttle is not None:
                throttle.mark_finished()

    raise ProviderError("request failed after retry")
