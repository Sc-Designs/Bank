from uuid import UUID
from fastapi import HTTPException, status
import psycopg

from ...db.db import get_connection
from .UserBallanceSchema import UserBallanceSchema
from .UserValidator import money_add_request
from .UserBallanceSchema import money_add_response
import logging

UserBallanceSchema()

logger = logging.getLogger(__name__)

class UserBalanceService:
    @staticmethod
    def create_balance_account(
        userid: UUID | str,
        cursor: psycopg.Cursor | None = None,
    ) -> None:
        query = "INSERT INTO user_balance (user_id, balance) VALUES (%s, 0.00)"
        if cursor is not None:
            cursor.execute(query, (userid,))
            return

        with get_connection() as connection:
            with connection.cursor() as local_cursor:
                local_cursor.execute(query, (userid,))


def money_add(payload: money_add_request) -> money_add_response:
    balance = float(payload.balance)
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                        UPDATE user_balance
                        SET balance = balance + (%s)
                        WHERE user_id = (%s)
                        RETURNING user_id, balance;
                    """,
                    (balance, payload.user_id)
                )
                recipet = cursor.fetchone()
                if recipet is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Something went wrong in Deposit Amount!"
                    )
    except psycopg.Error as error:
        logger.error(
                    "amount deposit operation failed (type=%s, sqlstate=%s)",
                    type(error).__name__,
                    error.sqlstate,
                )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="amount deposit service are unavailable for now, Please try again later!"
        )
    return money_add_response(
        user_id=str(recipet[0]),
        balance=recipet[1]
    )