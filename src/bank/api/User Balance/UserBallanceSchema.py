from ...db.db import get_connection


def UserBallanceSchema():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_balance (
                user_id UUID,
                balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
                transation UUID[] NOT NULL DEFAULT '{}',
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                FOREIGN KEY (user_id) REFERENCES user_acc(id),
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
