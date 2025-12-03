import logging

from fastapi import HTTPException, Request
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.core.exceptions.auth.exceptions import (
    FailedAuthorizationException,
    FailedLoginException,
)
from app.core.exceptions.base.exceptions import (
    ExceptionWithStatusAndDetail,
    ServiceUnavailableException,
)


class HarmixAPIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Harmix API key for every request."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow docs path without API key
        if path in settings.DOCS_PUBLIC_PATHS:
            return await call_next(request)

        # OPTIONS request -> skip API key checking
        if request.method == "OPTIONS":
            return await call_next(request)

        api_key = request.headers.get("api-key")

        if api_key != settings.HARMIX_API_KEY:
            exc = FailedAuthorizationException("API key is invalid")

            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        return await call_next(request)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except ExceptionWithStatusAndDetail as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail},
            )

        except SQLAlchemyOperationalError:
            logging.warning("Too many connections to the database are open.")
            exc = ServiceUnavailableException()
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        except SQLAlchemyTimeoutError:
            logging.warning("Database connection timed out.")
            exc = ServiceUnavailableException()
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        except HTTPException as e:
            raise e

        except Exception:
            logging.error("Internal error occurred", exc_info=True)

            exc = ServiceUnavailableException()
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
