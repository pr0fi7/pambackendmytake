from fastapi import status

from src.common.exceptions.base_exception import BaseHTTPException


class ConversationNotFoundError(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Conversation not found."
