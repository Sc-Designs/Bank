import logging

import psycopg
from fastapi import HTTPException, status

from ..db.db import get_connection
from ..utils.auth_utils import hash_password
from ..validators.user_validator import RegisteredUserResponse, RegisterUserRequest

logger = logging.getLogger(__name__)


def register_user(payload: RegisterUserRequest) -> RegisteredUserResponse:
    password_hash = hash_password(payload.password)

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_acc (email, display_name, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, display_name
                    """,
                    (payload.email, payload.display_name, password_hash),
                )
                user = cursor.fetchone()
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Registration failed to create user record",
                    )

                cursor.execute(
                    "INSERT INTO user_balance (user_id, balance) VALUES (%s, 0.00)",
                    (user[0],),
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

    return RegisteredUserResponse(
        id=str(user[0]),
        email=user[1],
        display_name=user[2],
    )
