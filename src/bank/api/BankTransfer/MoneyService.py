import uuid
from .MoneyValidator import money_request_validator
from .MoneySchema import money_responce
from ...db.db import get_connection
import psycopg
from fastapi import HTTPException, status

def send_money(payload: money_request_validator) -> money_responce:
    order_id = uuid.uuid4()
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                """
                INSERT INTO BankTransfer (orderid, accountdetail, sender, receiver, currency, status, mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (order_id, payload.account_details, payload.sender_id, payload.reciver_id, payload.currency, payload.status, payload.mode)
                )
                money_recipet = cursor.fetchone()
                if money_recipet is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="BankTransfer failed to send money to your desire account"
                    ) 
    except :
        raise



