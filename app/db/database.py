import psycopg2
import logging
from dotenv import load_dotenv
import os
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent.parent / "config" / ".env"
load_dotenv(dotenv_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            options="-c client_encoding=UTF8"
        )
        logger.info("✅ Database connection successful")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"❌ OperationalError: {e}")
        raise
    except psycopg2.DatabaseError as e:
        logger.error(f"❌ DatabaseError: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise
