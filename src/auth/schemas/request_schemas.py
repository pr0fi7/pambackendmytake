import re

from pydantic import field_validator, BaseModel


class LoginInput(BaseModel):
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
        if re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return email

        raise ValueError(f'Email address "{email}" is invalid')
