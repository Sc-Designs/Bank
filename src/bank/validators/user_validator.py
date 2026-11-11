import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class RegisteredUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
