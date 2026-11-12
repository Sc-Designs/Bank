from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class money_request_validator(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    order_id: UUID
    account_details: UUID | None = None
    sender_id: UUID | None = None
    reciver_id: UUID | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: Literal["pending", "posted", "reversed", "failed"] = "pending"
    mode: str | None = Field(default=None, max_length=4)