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
                currency CHAR(3) NOT NULL DEFAULT 'USD',
                status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','posted','reversed','failed')),
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
