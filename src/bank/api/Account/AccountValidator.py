import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class bank_account_register_request(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=12, max_length=20)
    display_name: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate(cls, value: str) -> str:
        value = value.lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value
