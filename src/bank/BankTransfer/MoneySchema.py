from ..db.db import get_connection


def BankTransfer_Schema():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BankTransfer (
                OrderID int PRIMARY KEY,
                AccountDetail int,
                Sender int NULL,
                Reciver int NULL,
                Mode VARCHAR(20),
                FOREIGN KEY (AccountDetail) REFERENCES user_acc(id),
                FOREIGN KEY (Sender) REFERENCES user_acc(id)
                FOREIGN KEY (Reciver) REFERENCES user_acc(id)
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