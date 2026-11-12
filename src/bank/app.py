import logging

from fastapi import FastAPI

from .db.db import get_connection
from .router import api_router
from .api.Account.AccountRoutes import route as account_opening
from .api.BankTransfer.BankTransferController import route as bank_transfer_router

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Simple Bank CRUD API",
        version="0.1.0",
        description="Learning-project banking API with FastAPI and PostgreSQL.",
    )

    @application.on_event("startup")
    async def startup():
        try:
            connection = get_connection()
            connection.execute("SELECT 1")
            connection.close()

            logger.info("PostgreSQL connected successfully")

        except Exception:
            logger.exception("PostgreSQL connection failed")
            raise

    application.include_router(api_router)

    return application


app = create_app()

app.include_router(account_opening)
app.include_router(bank_transfer_router)
