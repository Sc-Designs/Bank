import hashlib
import logging
import re
import secrets

import psycopg
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..db.db import get_connection

logger = logging.getLogger(__name__)


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class RegisteredUserResponse(BaseModel):
    id: str
    email: str
    display_name: str


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def register_user(payload: RegisterUserRequest) -> RegisteredUserResponse:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_acc (email, display_name, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, email, display_name
                    """,
                    (payload.email, payload.display_name, _hash_password(payload.password)),
                )
                user = cursor.fetchone()
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
        id=str(user[0]), email=user[1], display_name=user[2]
    )
