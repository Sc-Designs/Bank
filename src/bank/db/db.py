import logging

import psycopg

from ..config.config import settings

logger = logging.getLogger("uvicorn.error")


def get_connection() -> psycopg.Connection:
    try:
        connection = psycopg.connect(settings.POSTGRES_CONFIG)
        logger.info("PostgreSQL connection established")
        return connection
    except psycopg.Error:
        logger.exception("Failed to connect to PostgreSQL database")
        raise
