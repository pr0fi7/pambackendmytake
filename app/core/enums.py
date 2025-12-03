import datetime
from enum import Enum, auto

from app.config import settings


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
            self.ACCESS: settings.ACCESS_TOKEN_LIFETIME,
            self.REFRESH: settings.REFRESH_TOKEN_LIFETIME,
        }

        try:
            return token_lifetime[self]
        except KeyError:
            raise ValueError("This token type does not have lifetime")


class VMScriptNameEnum(Enum):
    CREATE_CLIENT = "create_client.sh"


class RunVariant(str, Enum):
    auto = "auto"
    manual = "manual"


class RepeatType(str, Enum):
    once = "once"
    every = "every"


class RepeatEvery(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    hour = "hour"


class Meridiem(str, Enum):
    AM = "AM"
    PM = "PM"


class WorkflowRunStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
