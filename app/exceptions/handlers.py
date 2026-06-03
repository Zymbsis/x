from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AppError


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
