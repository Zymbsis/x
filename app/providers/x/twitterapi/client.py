import logging
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection

from app.config import settings
from app.exceptions.base import ServiceUnavailableError
from app.providers.x.throttle import RequestGapThrottle

logger = logging.getLogger(__name__)


async def initialize(app: FastAPI) -> None:
    if settings.twitterapi_io.rate_limit_enabled:
        app.state.twitterapi_throttle = RequestGapThrottle(settings.twitterapi_io.period_sec)
    else:
        app.state.twitterapi_throttle = None
    app.state.twitterapi_client = httpx.AsyncClient(
        base_url=settings.twitterapi_io.base_url,
        headers={"X-API-Key": settings.twitterapi_io.api_key},
    )
    logger.info("twitterapi.io client initialized")


async def shutdown(app: FastAPI) -> None:
    client: httpx.AsyncClient | None = getattr(app.state, "twitterapi_client", None)
    if client is not None:
        await client.aclose()
        logger.info("twitterapi.io client shut down")


def get_twitterapi_client(conn: HTTPConnection) -> httpx.AsyncClient:
    client: httpx.AsyncClient | None = getattr(conn.app.state, "twitterapi_client", None)
    if client is None:
        raise ServiceUnavailableError("twitterapi.io client is not initialized")
    return client


def get_twitterapi_throttle(conn: HTTPConnection) -> RequestGapThrottle | None:
    return getattr(conn.app.state, "twitterapi_throttle", None)


TwitterApiClientDep = Annotated[httpx.AsyncClient, Depends(get_twitterapi_client)]
TwitterApiThrottleDep = Annotated[RequestGapThrottle | None, Depends(get_twitterapi_throttle)]
