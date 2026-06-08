import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

from app.exceptions.base import AppError

logger = logging.getLogger(__name__)


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc

    detail = f"{exc.__class__.__name__}: {exc.message}"
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(detail)
    else:
        logger.warning(detail)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
