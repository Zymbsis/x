import logging
from typing import Annotated

from aiolimiter import AsyncLimiter
from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection

from app.config import settings

logger = logging.getLogger(__name__)


async def initialize(app: FastAPI) -> None:
    if settings.twitterapi_io.rate_limit_enabled:
        app.state.twitterapi_limiter: AsyncLimiter | None = AsyncLimiter(
            max_rate=settings.twitterapi_io.max_requests, time_period=settings.twitterapi_io.period_sec
        )
        logger.info("twitterapi limiter initialized")
    else:
        app.state.twitterapi_limiter = None
        logger.info("twitterapi limiter disabled")


async def get_twitterapi_limiter(conn: HTTPConnection) -> AsyncLimiter | None:
    return getattr(conn.app.state, "twitterapi_limiter", None)


TwitterApiLimiterDep = Annotated[AsyncLimiter, Depends(get_twitterapi_limiter)]
