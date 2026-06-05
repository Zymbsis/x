import logging
from typing import Any

import httpx
from aiolimiter import AsyncLimiter
from tenacity import RetryCallState, retry, retry_if_exception, stop_after_attempt, wait_exponential, wait_random

from app.exceptions.base import ProviderError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable_http_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return False


def _log_retry(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception()
    path = retry_state.kwargs.get("path", "unknown")
    detail = f"request to {path} failed: {exc}, retrying (attempt {retry_state.attempt_number})"
    logger.warning(detail)


def _raise_provider_error(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception()
    detail = f"request failed: {exc}"
    raise ProviderError(detail) from exc


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=10) + wait_random(0, 0.5),
    retry=retry_if_exception(_is_retryable_http_error),
    before_sleep=_log_retry,
    retry_error_callback=_raise_provider_error,
)
async def get_json(
    *,
    client: httpx.AsyncClient,
    path: str,
    params: dict[str, Any],
    limiter: AsyncLimiter | None = None,
) -> dict[str, Any]:
    if limiter is not None:
        async with limiter:
            response = await client.get(path, params=params)
    else:
        response = await client.get(path, params=params)

    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        detail = f"request failed: {exc}"
        raise ProviderError(detail) from exc
