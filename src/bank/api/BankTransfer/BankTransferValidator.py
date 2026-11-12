from pydantic import BaseModel, field_validator
import uuid


class MoneyProps(BaseModel):
    OrderID: uuid.UUID
    AccountDetail: uuid.UUID
    Sender: uuid.UUID | None = None
    Receiver: uuid.UUID | None = None
    currency: str = "INR"
    status: str = "pending"
    Mode: str | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError("currency must be exactly 3 characters (CHAR(3))")
        return v.upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ("pending", "posted", "reversed", "failed")
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got '{v}'")
        return v

    @field_validator("Mode")
    @classmethod
    def validate_mode(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 20:
            raise ValueError("Mode must be at most 20 characters (VARCHAR(20))")
        return v
