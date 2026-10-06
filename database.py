import sqlite3
from datetime import datetime, timezone
from contextlib import closing
from config import DB_PATH

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs(
                    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

def create_job(document_id: str):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            cursor = connection.cursor()
            timestamp = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT INTO jobs (document_id, status, created_at) VALUES (?,?,?)
                """,
                (document_id, "processing",timestamp)
            )
            row_id = cursor.lastrowid

    return row_id

def update_job_status(job_id: int, status: str):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
        
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE jobs 
                SET status = ? 
                WHERE job_id = ?
                """, 
                (status, job_id)
            )

def get_job(job_id: int):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE job_id = ?", 
            (job_id,)
        )
        row = cursor.fetchone()
    return row