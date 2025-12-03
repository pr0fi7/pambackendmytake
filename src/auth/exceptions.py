from fastapi import status

from src.common.exceptions.base_exception import BaseHTTPException, ExceptionWithStatusAndDetail


class NotAuthenticatedException(ExceptionWithStatusAndDetail):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'Not authenticated')


class FailedAuthorizationException(ExceptionWithStatusAndDetail):
    def __init__(self, message: str):
        super().__init__(status.HTTP_401_UNAUTHORIZED, f'Authorization failed, error: {message}')


class InvalidAuthorizationSchemeException(ExceptionWithStatusAndDetail):
    def __init__(self, schema: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_CONTENT, f'Invalid authorization scheme "{schema}"')


class UserNotFoundByIdOrDeletedException(ExceptionWithStatusAndDetail):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, f'User could not be found or was deleted')


class FailedLoginException(ExceptionWithStatusAndDetail):
    def __init__(self):
        # Return generic response not to uncover data in the database
        super().__init__(status.HTTP_422_UNPROCESSABLE_CONTENT, f'This login details are incorrect. Please try again.')
