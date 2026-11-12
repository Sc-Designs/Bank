from .BankTransferSchema import BankTransfer_Schema
from ...db.db import get_connection
from .BankTransferValidator import MoneyProps

conn = get_connection()


BankTransfer_Schema()


class MoneyService:
    def CreateMoneyTransfer(Data: MoneyProps):
        conn.execute("""
            INSERT INTO BankTransfer (
                OrderID, AccountDetail, Sender, Receiver,
                currency, status, Mode
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            );
        """, (
            Data.OrderID,
            Data.AccountDetail,
            Data.Sender,
            Data.Receiver,
            Data.currency,
            Data.status,
            Data.Mode
        ))
        
        conn.commit()