import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
load_dotenv() 

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME",     "rinsetu"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
}

def get_connection():
    """Return a new psycopg2 connection with RealDictCursor."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_db():
    """Run schema.sql on startup to create tables if they don't exist."""
    schema_path =os.path.abspath( os.path.join(os.path.dirname(__file__), "..","..", "sql", "schema.sql"))
    with open(schema_path, "r") as f:
        sql = f.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("[RinSetu] Database initialised.")
    finally:
        conn.close()
