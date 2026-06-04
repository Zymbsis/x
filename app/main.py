import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.logging import setup_logging
from app.exceptions.base import AppError
from app.exceptions.handlers import app_error_handler
from app.providers.x.twitterapi import client as twitterapi
from app.routers import x_collection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.environment)

    await twitterapi.initialize(app)
    logger.info("Application startup complete")
    yield
    await twitterapi.shutdown(app)


app = FastAPI(lifespan=lifespan)

app.include_router(x_collection.router)
app.add_exception_handler(AppError, app_error_handler)
