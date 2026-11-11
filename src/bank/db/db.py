import psycopg

from ..config.config import settings


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.POSTGRES_CONFIG)
