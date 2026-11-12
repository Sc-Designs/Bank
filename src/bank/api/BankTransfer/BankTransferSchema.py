from ...db.db import get_connection
from pydantic import BaseModel

def BankTransfer_Schema():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BankTransfer (
                OrderID UUID PRIMARY KEY,
                AccountDetail UUID,
                Sender UUID NULL,
                Receiver UUID NULL,
                currency CHAR(3) NOT NULL DEFAULT 'INR',
                status TEXT NOT NULL DEFAULT 'pending',
                Mode VARCHAR(20),
                FOREIGN KEY (AccountDetail) REFERENCES user_acc(id),
                FOREIGN KEY (Sender) REFERENCES user_acc(id),
                FOREIGN KEY (Receiver) REFERENCES user_acc(id)
            );
        """)

        conn.commit()
        print("Table 'money' created successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating table: {e}")

    finally:
        if conn:
            conn.close()

class money_responce(BaseModel):
    order_id: str
    reciver_id: str
    sender_id: str
    currency: str
    status: str
    mode: str
