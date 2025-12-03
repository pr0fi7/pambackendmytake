import datetime
from enum import Enum, auto

from src.auth import constants


class TokenTypeEnum(Enum):
    ACCESS = auto()
    REFRESH = auto()

    def get_token_lifetime(self) -> datetime.timedelta:
        """
        Get lifetime of for token type
        :raise ValueError: when token type does not have lifetime
        :return: timedelta object for the lifetime
        """
        token_lifetime = {
            self.ACCESS: constants.ACCESS_TOKEN_LIFETIME,
            self.REFRESH: constants.REFRESH_TOKEN_LIFETIME,
        }

        try:
            return token_lifetime[self]
        except KeyError:
            raise ValueError("This token type does not have lifetime")
