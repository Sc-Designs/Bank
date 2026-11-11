from fastapi import APIRouter

route = APIRouter()

route.get("/accounts")
def create_account(account_data: dict):
    print(f"Creating account with data: {account_data}")

