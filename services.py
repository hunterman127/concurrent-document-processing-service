# services.py

import time


async def download_document(document_id: str) -> str:
    """Download a document from remote storage."""
    ...


def save_original(document: str) -> None:
    """Save the original document to legacy storage."""
    time.sleep(1)


def extract_text(document: str) -> str:
    """CPU-intensive document parsing."""
    ...
    return "extracted text"


async def store_text(document_id: str, text: str) -> None:
    """Store extracted text in the database."""
    ...