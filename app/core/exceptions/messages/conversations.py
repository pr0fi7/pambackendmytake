from fastapi import status

from app.core.exceptions.base.exceptions import BaseHTTPException


class ConversationNotFoundError(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Conversation not found."
