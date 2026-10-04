# pipeline.py
import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed

from services import (
    download_document,
    save_original,
    extract_text,
    store_text,
)

EXTRACTION_TIMEOUT = 10

process_pool = ProcessPoolExecutor(max_workers=8)

extraction_limit = asyncio.Semaphore(3)

async def cleanup_extraction(cpu_future):
    try:
        await asyncio.shield(cpu_future)
    finally:
        extraction_limit.release()

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
        async with asyncio.timeout(EXTRACTION_TIMEOUT):
            await extraction_limit.acquire()
            cpu_future = loop.run_in_executor(
                process_pool,
                extract_text,
                document
            )

            try:
                extracted = await asyncio.shield(cpu_future)
                extraction_limit.release()


            except asyncio.CancelledError:
                asyncio.create_task(
                    cleanup_extraction(cpu_future)
                )
                raise

            except Exception:
                extraction_limit.release()
                raise

            await store_text(document_id, extracted)
    finally:
        await backup

async def process_batch(document_ids: list[str]) -> dict[str, str]:
    tasks = {}

    for document_id in document_ids:
        task = asyncio.create_task(
            process_document(document_id)
        )

        tasks[task] = document_id

    results = {}

    async for completed_task in asyncio.as_completed(tasks):
        document_id = tasks[completed_task]

        try:
            await completed_task
            results[document_id] = "success"
        except Exception:
            results[document_id] = "failed"

    return results