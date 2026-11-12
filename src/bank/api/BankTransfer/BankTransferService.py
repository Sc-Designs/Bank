import logging
import uuid
from uuid import UUID

import psycopg
from fastapi import HTTPException, status

from ...db.db import get_connection
from .BankTransferSchema import BankTransferResponse, BankTransfer_Schema
from .BankTransferValidator import BankTransferRequest

logger = logging.getLogger(__name__)

BankTransfer_Schema()


def _row_to_response(row: tuple) -> BankTransferResponse:
    return BankTransferResponse(
        order_id=str(row[0]),
        account_detail=str(row[1]) if row[1] is not None else None,
        sender_id=str(row[2]) if row[2] is not None else None,
        receiver_id=str(row[3]) if row[3] is not None else None,
        amount=float(row[4]),
        currency=row[5],
        status=row[6],
        mode=row[7],
    )


def create_bank_transfer(payload: BankTransferRequest) -> BankTransferResponse:
    order_id = payload.order_id or uuid.uuid4()

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO BankTransfer (
                        OrderID, AccountDetail, Sender, Receiver,
                        amount, currency, status, Mode
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING OrderID, AccountDetail, Sender, Receiver, Amount, currency, status, Mode
                    """,
                    (
                        order_id,
                        payload.account_detail,
                        payload.sender_id,
                        payload.receiver_id,
                        payload.amount,
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

    return _row_to_response(transfer)


def get_bank_transfer_by_id(order_id: UUID) -> BankTransferResponse | None:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT OrderID, AccountDetail, Sender, Receiver, Amount, currency, status, Mode
                    FROM BankTransfer
                    WHERE OrderID = %s
                    """,
                    (order_id,),
                )
                transfer = cursor.fetchone()
    except psycopg.Error as error:
        logger.error(
            "BankTransfer fetch failed (type=%s, sqlstate=%s)",
            type(error).__name__,
            error.sqlstate,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BankTransfer is temporarily unavailable",
        ) from error

    return _row_to_response(transfer) if transfer is not None else None


def get_bank_transfers_by_user(user_id: UUID) -> list[BankTransferResponse]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT OrderID, AccountDetail, Sender, Receiver, Amount, currency, status, Mode
                    FROM BankTransfer
                    WHERE AccountDetail = %s OR Sender = %s OR Receiver = %s
                    """,
                    (user_id, user_id, user_id),
                )
                rows = cursor.fetchall()
    except psycopg.Error as error:
        logger.error(
            "BankTransfer list failed (type=%s, sqlstate=%s)",
            type(error).__name__,
            error.sqlstate,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BankTransfer is temporarily unavailable",
        ) from error

    return [_row_to_response(row) for row in rows]


def update_bank_transfer_status(
    order_id: UUID,
    new_status: str,
) -> BankTransferResponse | None:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE BankTransfer
                    SET status = %s
                    WHERE OrderID = %s
                    RETURNING OrderID, AccountDetail, Sender, Receiver, Amount, currency, status, Mode
                    """,
                    (new_status, order_id),
                )
                transfer = cursor.fetchone()
    except psycopg.Error as error:
        logger.error(
            "BankTransfer status update failed (type=%s, sqlstate=%s)",
            type(error).__name__,
            error.sqlstate,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BankTransfer is temporarily unavailable",
        ) from error

    return _row_to_response(transfer) if transfer is not None else None
