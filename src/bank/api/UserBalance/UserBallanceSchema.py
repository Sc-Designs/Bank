from ...db.db import get_connection
from pydantic import BaseModel

def UserBallanceSchema():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_balance (
                user_id UUID PRIMARY KEY,
                balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                FOREIGN KEY (user_id) REFERENCES user_acc(id) ON DELETE RESTRICT
            );
        """)

        conn.commit()
        print("user table created successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating table: {e}")

    finally:
        if conn:
            conn.close()


class money_add_response(BaseModel):
    user_id: str
    balance: float