from fastapi import APIRouter, status

from .BankTransferSchema import BankTransferResponse
from .BankTransferService import create_bank_transfer
from .BankTransferValidator import BankTransferRequest

route = APIRouter(prefix="/bank-transfer", tags=["bank-transfer"])


@route.post(
    "/create",
    response_model=BankTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def bank_transfer(payload: BankTransferRequest) -> BankTransferResponse:
    return create_bank_transfer(payload)
