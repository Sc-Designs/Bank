from uuid import UUID

from fastapi import HTTPException, status

from .BankTransferSchema import BankTransferResponse
from .BankTransferService import (
    create_bank_transfer,
    get_bank_transfer_by_id,
    get_bank_transfers_by_user,
    update_bank_transfer_status,
)
from .BankTransferValidator import BankTransferRequest, BankTransferStatusUpdate


class BankTransferController:
    @staticmethod
    def create_transfer(payload: BankTransferRequest) -> BankTransferResponse:
        validated = BankTransferRequest.model_validate(payload)
        return create_bank_transfer(validated)

    @staticmethod
    def get_transfer(order_id: UUID) -> BankTransferResponse:
        transfer = get_bank_transfer_by_id(order_id)
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank transfer order not found",
            )
        return transfer

    @staticmethod
    def list_user_transfers(user_id: UUID) -> list[BankTransferResponse]:
        return get_bank_transfers_by_user(user_id)

    @staticmethod
    def update_transfer_status(
        order_id: UUID,
        payload: BankTransferStatusUpdate,
    ) -> BankTransferResponse:
        transfer = update_bank_transfer_status(order_id, payload.status)
        if transfer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank transfer order not found",
            )
        return transfer
