from pydantic import BaseModel

class bank_account_register_response(BaseModel):
    id: str
    email: str
    display_name: str