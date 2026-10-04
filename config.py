from dotenv import load_dotenv
import os

load_dotenv()

EXTRACTION_TIMEOUT = float(os.getenv("EXTRACTION_TIMEOUT", 10))
EXTRACTION_CONCURRENCY = int(os.getenv("EXTRACTION_CONCURRENCY", 3))
PROCESS_POOL_WORKERS = int(os.getenv("PROCESS_POOL_WORKERS", 8))