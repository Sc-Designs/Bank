import psycopg

from ..config.config import settings


def get_connection() -> psycopg.Connection:
    try:
        conn = psycopg.connect(settings.POSTGRES_CONFIG)
        print("Db Connected")
    except Exception as e:
        raise e
    
