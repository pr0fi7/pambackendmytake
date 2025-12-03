from datetime import datetime
from typing import Union, Any

from pydantic import BaseModel, field_validator

from src.auth.schemas.enums.token_type_enum import TokenTypeEnum


class TokenPayload(BaseModel):
    iss: str
    exp: datetime
    iat: datetime
    sub: str
    token_type: TokenTypeEnum

    @field_validator('token_type', mode='before')
    def validate_token_type(cls, value: Union[str, TokenTypeEnum]) -> TokenTypeEnum:
        """
        Construct token_type property from str and TokenTypeEnum
        :param value: input value
        :raise ValueError: if token type is not supported
        :return: token type enum object
        """
        if isinstance(value, str):
            try:
                return TokenTypeEnum[value]
            except ValueError:
                raise ValueError(f'Invalid value passed for token type: {value}')
        return value

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        """Override method to convert TokenTypeEnum to a string representation"""
        data = super(TokenPayload, self).model_dump(*args, **kwargs)
        data['token_type'] = self.token_type.name
        return data
