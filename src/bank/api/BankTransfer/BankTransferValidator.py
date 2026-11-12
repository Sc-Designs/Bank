from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BankTransferRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, revalidate_instances="always")

    order_id: UUID | None = None
    account_detail: UUID | None = None
    sender_id: UUID | None = None
    receiver_id: UUID | None = None
    amount: float
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: Literal["pending", "posted", "reversed", "failed"] = "pending"
    mode: str | None = Field(default=None, max_length=20)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()
        if not value.isalpha() or len(value) != 3:
            raise ValueError("currency must be a 3-letter ISO code (CHAR(3))")
        return value

    @model_validator(mode="after")
    def validate_accounts(self) -> "BankTransferRequest":
        if (
            self.account_detail is None
            and self.sender_id is None
            and self.receiver_id is None
        ):
            raise ValueError(
                "At least one of account_detail, sender_id, or receiver_id is required"
            )

        if (
            self.sender_id is not None
            and self.receiver_id is not None
            and self.sender_id == self.receiver_id
        ):
            raise ValueError("Sender and receiver cannot be the same account")

        return self


class BankTransferStatusUpdate(BaseModel):
    status: Literal["pending", "posted", "reversed", "failed"]
