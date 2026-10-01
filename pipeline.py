# pipeline.py
import asyncio
from concurrent.futures import ProcessPoolExecutor

from services import (
    download_document,
    save_original,
    extract_text,
    store_text,
)

process_pool = ProcessPoolExecutor(max_workers=8)

extraction_limit = asyncio.Semaphore(3)

async def process_document(document_id: str) -> None:
    loop = asyncio.get_running_loop()

    document = await download_document(document_id)


    backup = asyncio.create_task(
        asyncio.to_thread(
            save_original,
            document
        )
    )
    try:
        async with asyncio.timeout(10):
            async with extraction_limit:
                extracted = await loop.run_in_executor(
                    process_pool,
                    extract_text,
                    document
                )

            await store_text(document_id, extracted)

    finally:
        await backup