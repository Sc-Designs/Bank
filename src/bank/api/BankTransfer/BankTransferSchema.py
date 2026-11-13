from pydantic import BaseModel

from ...db.db import get_connection


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
                amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (amount >= 0),
                currency CHAR(3) NOT NULL DEFAULT 'INR',
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'posted', 'reversed', 'failed')),
                Mode VARCHAR(20),
                FOREIGN KEY (AccountDetail) REFERENCES user_acc(id),
                FOREIGN KEY (Sender) REFERENCES user_acc(id),
                FOREIGN KEY (Receiver) REFERENCES user_acc(id)
            );
        """)

        conn.commit()
        print("Table 'BankTransfer' created successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating table: {e}")

    finally:
        if conn:
            conn.close()


class BankTransferResponse(BaseModel):
    order_id: str
    account_detail: str | None = None
    sender_id: str | None = None
    receiver_id: str | None = None
    amount: float
    currency: str
    status: str
    mode: str | None = None
    sender_display_name: str
    receiver_display_name: str
