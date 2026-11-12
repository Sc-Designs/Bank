from uuid import UUID

from fastapi import APIRouter, status

from .BankTransferController import BankTransferController
from .BankTransferSchema import BankTransferResponse
from .BankTransferValidator import BankTransferRequest, BankTransferStatusUpdate

route = APIRouter(prefix="/bank-transfer", tags=["bank-transfer"])


@route.post(
    "/create",
    response_model=BankTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transfer_route(payload: BankTransferRequest) -> BankTransferResponse:
    return BankTransferController.create_transfer(payload)


@route.get(
    "/{order_id}",
    response_model=BankTransferResponse,
    status_code=status.HTTP_200_OK,
)
def get_transfer_route(order_id: UUID) -> BankTransferResponse:
    return BankTransferController.get_transfer(order_id)


@route.get(
    "/user/{user_id}",
    response_model=list[BankTransferResponse],
    status_code=status.HTTP_200_OK,
)
def list_user_transfers_route(user_id: UUID) -> list[BankTransferResponse]:
    return BankTransferController.list_user_transfers(user_id)


@route.patch(
    "/{order_id}/status",
    response_model=BankTransferResponse,
    status_code=status.HTTP_200_OK,
)
def update_transfer_status_route(
    order_id: UUID,
    payload: BankTransferStatusUpdate,
) -> BankTransferResponse:
    return BankTransferController.update_transfer_status(order_id, payload)
