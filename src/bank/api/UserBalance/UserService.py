from uuid import UUID

import psycopg

from ...db.db import get_connection
from .UserBallanceSchema import UserBallanceSchema

UserBallanceSchema()


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
