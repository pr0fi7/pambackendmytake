import re

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, email: str) -> str:
        """
        Validator for email field - matches against regular expression.

        :param email: Initial email value.
        :return: Valid email.
        :raise ValueError: in case of invalid email.
        """
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return email

        raise ValueError(f'Email address "{email}" is invalid')


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str


class RegisterRequest(BaseModel):
    email: str
    password: str

    name: str
    company_name: str | None = None
    position: str | None = None
