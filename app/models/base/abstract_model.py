from typing import Any, Iterable

from pydantic import BaseModel


class AbstractModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = False

    @classmethod
    def validate_positive_value(cls, value):
        if value < 1:
            raise ValueError("Field must be greater than 0.")
        return value

    @classmethod
    def model_validate(  # type: ignore
        cls: type["AbstractModel"],
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = True,
        context: dict[str, Any] | None = None,
    ) -> "Any":
        if obj is None:
            return None
        _result = super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
        return _result.model_copy()

    @classmethod
    def validate_list_model(cls, value: Iterable[Any]) -> list:
        return [cls.model_validate(item) for item in value]
