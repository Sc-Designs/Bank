from fastapi import APIRouter, status
from .AccountService import create_bank_account
from .AccountValidator import bank_account_register_request
from .AccountSchema import bank_account_register_response

route = APIRouter(prefix="/user", tags=["account"])

@route.post(
    "/create-accounts",
    response_model=bank_account_register_response,
    status_code=status.HTTP_201_CREATED,
)
def account_opening(payload: bank_account_register_request) -> bank_account_register_response:
    return create_bank_account(payload)

