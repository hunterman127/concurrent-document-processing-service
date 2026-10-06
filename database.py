import sqlite3
from datetime import datetime, timezone

def init_db():
    connection = sqlite3.connect("documents.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs(
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
""")
    connection.commit()
    connection.close()

def create_job(document_id: str):
    connection = sqlite3.connect("documents.db")
    cursor = connection.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO jobs (document_id, status, created_at) VALUES (?,?,?)
        """,
        (document_id, "processing",timestamp)
    )
    row_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return row_id

def update_job_status(job_id: int, status: str):
    connection = sqlite3.connect("documents.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE jobs SET status = ? WHERE job_id = ?
""", (status, job_id))

    connection.commit()
    connection.close()

def get_job(job_id: int):
    connection = sqlite3.connect("documents.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row_id = cursor.fetchone()
    connection.close()
    return row_id