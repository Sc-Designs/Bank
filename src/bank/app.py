from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from .db.db import get_connection
from .router import api_router
from .api.Account.AccountRoutes import route as account_opening

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(application: FastAPI):
    with get_connection() as connection:
        connection.execute("SELECT 1")
    logger.info("PostgreSQL startup check succeeded")
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Simple Bank CRUD API",
        version="0.1.0",
        description="Learning-project banking API with FastAPI and PostgreSQL.",
        lifespan=lifespan,
    )
    application.include_router(api_router)
    return application


app = create_app()

app.include_router(account_opening)