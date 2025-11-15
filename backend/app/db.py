import psycopg2
from .config import Config


def connect_db():
    """Create a new PostgreSQL connection using environment-based config."""
    return psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        port=Config.DB_PORT,
    )

