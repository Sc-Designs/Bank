from pydantic import BaseModel


class bank_account_register_response(BaseModel):
    id: str
    email: str
    display_name: str


from ...db.db import get_connection


def Account_Schema():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_acc (
               id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
               email VARCHAR(254) NOT NULL UNIQUE,
               display_name VARCHAR(100) NOT NULL,
               password_hash TEXT NOT NULL,
               is_active BOOLEAN NOT NULL DEFAULT TRUE,
               created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
               updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
        """)

        conn.commit()
        print("user Table created successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating table: {e}")

    finally:
        if conn:
            conn.close()
