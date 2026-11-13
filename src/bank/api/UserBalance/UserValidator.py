from pydantic import BaseModel, ConfigDict
from uuid import UUID
class money_add_request(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id : UUID
    balance: float