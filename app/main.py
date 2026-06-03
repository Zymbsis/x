import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.logging import setup_logging
from app.db import engine as pg
from app.exceptions.base import AppError
from app.exceptions.handlers import app_error_handler
from app.providers.x.twitterapi import client as twitterapi

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.environment)

    await pg.connect()
    await twitterapi.initialize(app)
    logger.info("Application startup complete")
    yield
    await twitterapi.shutdown(app)
    await pg.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
