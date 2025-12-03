from fastapi import status, HTTPException


class ExceptionWithStatusAndDetail(BaseException):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class ExceptionWithStatusAndDetailDict(HTTPException):
    def __init__(self, status_code: int, **kwargs):
        detail = kwargs
        super().__init__(status_code=status_code, detail=detail)


class BaseHTTPException(ExceptionWithStatusAndDetailDict):
    """
    Base class for all HTTP exceptions.
    :param status_code: (int) - HTTP status code.
    :param code: (int) - Harmix status code.
    :param status: (str) - Harmix status.
    :param message: (str) - Error message.
    :param details: (str) - Error details.
    """
    status_code = None
    code = None
    status = 'failure'
    message = ''
    details = ''
    extra_information = {}

    def __init__(self, **kwargs):
        details_dict = {
            'code': self.code,
            'status': self.status,
            'message': self.message,
            'details': self.details,
        }
        if self.extra_information:
            details_dict['extra_information'] = self.extra_information

        super().__init__(
            status_code=self.status_code,
            **details_dict,
            **kwargs,
        )


class ServiceUnavailableException(BaseHTTPException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = 'Harmix is unavailable at the moment.'
    details = 'We are sorry for the inconvenience. Please try again later. If the error persists, please contact ' \
              'Harmix Support at support@harmix.ai'
