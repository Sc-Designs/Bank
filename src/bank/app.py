from fastapi import FastAPI

from .router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Simple Bank CRUD API",
        version="0.1.0",
        description="Learning-project banking API with FastAPI and PostgreSQL.",
    )
    application.include_router(api_router)
    return application


app = create_app()
