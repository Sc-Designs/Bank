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
        sender_display_name=row[8],
        receiver_display_name=row[9],
    )

_TRANSFER_SELECT = """
    t.OrderID, t.AccountDetail, t.Sender, t.Receiver,
    t.Amount, t.currency, t.status, t.Mode,
    sender.display_name, receiver.display_name
"""

def create_bank_transfer(payload: BankTransferRequest) -> BankTransferResponse:
    if payload.sender_id is None or payload.receiver_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="sender_id and receiver_id are required",
        )

    if payload.sender_id == payload.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sender and receiver must be different accounts",
        )

    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transfer amount must be greater than zero",
        )

    order_id = payload.order_id or uuid.uuid4()

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # Lock both balance rows in consistent order for concurrent transfers.
                cursor.execute(
                    """
                    SELECT b.user_id, b.balance, a.display_name
                    FROM user_balance AS b
                    JOIN user_acc AS a ON a.id = b.user_id
                    WHERE b.user_id IN (%s, %s)
                    ORDER BY b.user_id
                    FOR UPDATE OF b
                    """,
                    (payload.sender_id, payload.receiver_id),
                )
                accounts = {
                    row[0]: {"balance": row[1], "display_name": row[2]}
                    for row in cursor.fetchall()
                }

                sender = accounts.get(payload.sender_id)
                receiver = accounts.get(payload.receiver_id)

                if sender is None or receiver is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Sender or receiver account not found",
                    )

                if sender["balance"] < payload.amount:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Insufficient funds",
                    )

                cursor.execute(
                    """
                    UPDATE user_balance
                    SET balance = balance - %s
                    WHERE user_id = %s
                    """,
                    (payload.amount, payload.sender_id),
                )
                cursor.execute(
                    """
                    UPDATE user_balance
                    SET balance = balance + %s
                    WHERE user_id = %s
                    """,
                    (payload.amount, payload.receiver_id),
                )
                cursor.execute(
                    """
                    INSERT INTO BankTransfer (
                        OrderID, AccountDetail, Sender, Receiver,
                        amount, currency, status, Mode
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING OrderID, AccountDetail, Sender, Receiver,
                    amount, currency, status, Mode
                    """,
                    (
                        order_id,
                        payload.account_detail,
                        payload.sender_id,
                        payload.receiver_id,
                        payload.amount,
                        payload.currency,
                        "posted",
                        payload.mode,
                    ),
                )
                transfer = cursor.fetchone()

                if transfer is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Failed to create transfer record",
                    )

                # Append names in the positions expected by _row_to_response().
                transfer = (
                    *transfer,
                    sender["display_name"],
                    receiver["display_name"],
                )

    except HTTPException:
        raise
    except psycopg.errors.ForeignKeyViolation as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced account does not exist",
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
                    f"""
                    SELECT {_TRANSFER_SELECT}
                    FROM BankTransfer AS t
                    LEFT JOIN user_acc AS sender ON sender.id = t.Sender
                    LEFT JOIN user_acc AS receiver ON receiver.id = t.Receiver
                    WHERE t.OrderID = %s
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
                    f"""
                    SELECT {_TRANSFER_SELECT}
                    FROM BankTransfer AS t
                    LEFT JOIN user_acc AS sender ON sender.id = t.Sender
                    LEFT JOIN user_acc AS receiver ON receiver.id = t.Receiver
                    WHERE t.AccountDetail = %s
                       OR t.Sender = %s
                       OR t.Receiver = %s
                    ORDER BY t.OrderID DESC
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
                    f"""
                    UPDATE BankTransfer AS t
                    SET status = %s
                    WHERE t.OrderID = %s
                    RETURNING
                        t.OrderID, t.AccountDetail, t.Sender, t.Receiver,
                        t.Amount, t.currency, t.status, t.Mode,
                        (SELECT a.display_name
                         FROM user_acc AS a WHERE a.id = t.Sender),
                        (SELECT a.display_name
                        FROM user_acc AS a WHERE a.id = t.Receiver)
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