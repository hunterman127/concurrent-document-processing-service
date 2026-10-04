# pipeline.py
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging

from services import (
    download_document,
    save_original,
    extract_text,
    store_text,
)

from config import (
    EXTRACTION_TIMEOUT,
    EXTRACTION_CONCURRENCY,
    PROCESS_POOL_WORKERS,
)

logger = logging.getLogger(__name__)

process_pool = ProcessPoolExecutor(max_workers=PROCESS_POOL_WORKERS)

extraction_limit = asyncio.Semaphore(EXTRACTION_CONCURRENCY)

async def cleanup_extraction(cpu_future):
    try:
        await asyncio.shield(cpu_future)
    finally:
        extraction_limit.release()

async def process_document(document_id: str) -> None:
    loop = asyncio.get_running_loop()
    logger.info("Download started for document %s", document_id)
    document = await download_document(document_id)
    logger.info("Download completed for document %s", document_id)

    logger.info("Backup started for document %s", document_id)
    backup = asyncio.create_task(
        asyncio.to_thread(
            save_original,
            document
        )
    )

    try:
        async with asyncio.timeout(EXTRACTION_TIMEOUT):
            await extraction_limit.acquire()
            release_here = True

            logger.info(
                "Extraction started for document %s",
                document_id
            )

            try:
                cpu_future = loop.run_in_executor(
                    process_pool,
                    extract_text,
                    document
                )

                try:
                    extracted = await asyncio.shield(cpu_future)

                    logger.info(
                        "Extraction completed for document %s",
                        document_id
                    )

                except asyncio.CancelledError:
                    asyncio.create_task(
                        cleanup_extraction(cpu_future)
                    )

                    release_here = False

                    logger.warning(
                        "Extraction interrupted for document %s; cleanup scheduled",
                        document_id
                    )

                    raise

            finally:
                if release_here:
                    extraction_limit.release()

            try:
                logger.info("Storage started for document %s", document_id)

                await store_text(document_id, extracted)

                logger.info("Storage completed for document %s", document_id)

            except Exception:
                logger.exception("Storage failed for document %s", document_id)
                raise

    except TimeoutError:
        logger.error("Processing timed out for document %s", document_id)
        raise

    except Exception:
        logger.exception(
            "Extraction failed for document %s",
            document_id
        )
        raise

    finally:
        try:
            await backup
            logger.info("Backup completed for document %s", document_id)
        except Exception:
            logger.exception("Backup failed for document %s", document_id)
            raise

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
            logger.exception("%s failed", document_id)
            results[document_id] = "failed"

    return results
