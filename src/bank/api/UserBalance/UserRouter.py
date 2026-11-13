from fastapi import APIRouter, status
from .UserBallanceSchema import money_add_response
from .UserValidator import money_add_request
from .UserService import money_add

route = APIRouter(prefix="/balance", tags=["balance"])

@route.post(
    "/add-money",
    response_model=money_add_response,
    status_code=status.HTTP_201_CREATED
)
def add_money_in_account(payload: money_add_request) -> money_add_response:
    return money_add(payload)