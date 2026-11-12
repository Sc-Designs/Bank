import psycopg
from fastapi import HTTPException, status
from ...db.db import get_connection
from ...utils.hashing_pass import password_hash as hash_password
from .AccountValidator import bank_account_register_request
from .AccountSchema import bank_account_register_response
import logging

logger = logging.getLogger(__name__)

from .AccountSchema import Account_Schema


from ...api.UserBalance import UserService


Account_Schema()


def create_bank_account(
    payload: bank_account_register_request,
) -> bank_account_register_response:
    password_digest = hash_password(payload.password)

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_acc (email, display_name, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, display_name
                    """,
                    (payload.email, payload.display_name, password_digest),
                )
                user = cursor.fetchone()
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Registration failed to create user record",
                    )
                UserService.UserBalanceService.create_balance_account(
                    user[0],
                    cursor=cursor,
                )
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from error
    except psycopg.Error as error:
        logger.error(
            "Registration database operation failed (type=%s, sqlstate=%s)",
            type(error).__name__,
            error.sqlstate,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration is temporarily unavailable",
        ) from error

    return bank_account_register_response(
        id=str(user[0]),
        email=user[1],
        display_name=user[2],
    )
