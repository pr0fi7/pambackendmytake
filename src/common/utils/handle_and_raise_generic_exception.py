import functools
import inspect
import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

from src.common.exceptions.base_exception import ServiceUnavailableException, ExceptionWithStatusAndDetail


def handle_and_raise_generic_exception(func):
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        # except BaseApiError as e:
        #     # Reports the error to alert service
        #     alert_service = AlertService()
        #     alert_service.report_general_error(
        #         session_id=kwargs.get('session_id', None),
        #         message_instance=e.message_prefix,
        #         client=kwargs.get('client', None),
        #         http_status=e.error.status_code,
        #         retries_number=e.retries_number,
        #         error_message=e.message
        #     )
        #     raise e.error
        except ExceptionWithStatusAndDetail as e:
            raise HTTPException(
                status_code=e.status_code,
                detail={'error': e.detail}
            ) from e
        except SQLAlchemyOperationalError:
            logging.warning('Too many connections to the database are open.')
            raise ServiceUnavailableException()
        except SQLAlchemyTimeoutError:
            logging.warning('Database connection timed out.')
            raise ServiceUnavailableException()
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logging.error('Internal error occurred', exc_info=True)
            # alert_service = AlertService()
            # alert_service.report_general_error(
            #     session_id=kwargs.get('session_id', None),
            #     message_instance="General",
            #     client=kwargs.get('client', None),
            #     http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     error_message=f"{e.__class__.__name__} - {e.args[0] if e.args else ''}"
            # )
            raise ServiceUnavailableException() from e

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await _wrapper(*args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        return _wrapper(*args, **kwargs)

    # Check if the function is asynchronous (async)
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
