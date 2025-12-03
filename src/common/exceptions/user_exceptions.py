from fastapi import status

from src.schemas.exceptions.base_exception import ExceptionWithStatusAndDetail


class UserNotFoundByIdOrDeletedException(ExceptionWithStatusAndDetail):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, f'User could not be found or was deleted')


class UserWasDeletedException(ExceptionWithStatusAndDetail):
    def __init__(self, user_id: int):
        super().__init__(status.HTTP_410_GONE, f'User with id "{user_id}" was deleted')


class UserAlreadyVerifiedException(ExceptionWithStatusAndDetail):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, 'User is already verified')


class CatalogForbiddenForUserException(ExceptionWithStatusAndDetail):
    def __init__(self, catalog_name: str):
        super().__init__(status.HTTP_403_FORBIDDEN, f'User does not have access to the catalog "{catalog_name}"')
