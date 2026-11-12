import logging
import uuid

import psycopg
from fastapi import HTTPException, status

from ...db.db import get_connection
from .BankTransferSchema import BankTransferResponse, BankTransfer_Schema
from .BankTransferValidator import BankTransferRequest

logger = logging.getLogger(__name__)

BankTransfer_Schema()


def create_bank_transfer(payload: BankTransferRequest) -> BankTransferResponse:
    if (
        payload.sender_id is not None
        and payload.receiver_id is not None
        and payload.sender_id == payload.receiver_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender and receiver cannot be the same account",
        )

    order_id = payload.order_id or uuid.uuid4()

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO BankTransfer (
                        OrderID, AccountDetail, Sender, Receiver,
                        currency, status, Mode
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING OrderID, AccountDetail, Sender, Receiver, currency, status, Mode
                    """,
                    (
                        order_id,
                        payload.account_detail,
                        payload.sender_id,
                        payload.receiver_id,
                        payload.currency,
                        payload.status,
                        payload.mode,
                    ),
                )
                transfer = cursor.fetchone()
                if transfer is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="BankTransfer failed to create transfer record",
                    )
    except psycopg.errors.ForeignKeyViolation as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced user account does not exist",
        ) from error
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transfer with this order_id already exists",
        ) from error
    except psycopg.Error as error:
        logger.error(
            "BankTransfer database operation failed (type=%s, sqlstate=%s)",
            type(error).__name__,
            error.sqlstate,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BankTransfer is temporarily unavailable",
        ) from error

    return BankTransferResponse(
        order_id=str(transfer[0]),
        account_detail=str(transfer[1]) if transfer[1] is not None else None,
        sender_id=str(transfer[2]) if transfer[2] is not None else None,
        receiver_id=str(transfer[3]) if transfer[3] is not None else None,
        currency=transfer[4],
        status=transfer[5],
        mode=transfer[6],
    )
