import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

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
        print("✅ Database connection successful")  # Başarı mesajı
        return conn
    except Exception as e:
        print(" Database connection failed:", str(e))  # Hata mesajını yazdır
        raise
