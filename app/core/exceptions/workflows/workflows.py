from fastapi import status

from app.core.exceptions.base.exceptions import BaseHTTPException


class WorkflowNotFoundError(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Workflow not found."
