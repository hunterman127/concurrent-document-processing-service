import asyncio
import pytest
import pipeline
from concurrent.futures import ThreadPoolExecutor
import time

async def fake_process_document(document_id):
    if document_id == "slow_doc":
        await asyncio.sleep(0.05)

    if document_id == "doc2":
        raise Exception("Failed")

async def fake_download_document(document_id):
    return "fake document"

def fake_original(document):
    pass

def fake_extract(document):
    time.sleep(.1)

@pytest.mark.asyncio
async def test_process_batch_continues_after_failure(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "process_document",
        fake_process_document
    )

    result = await pipeline.process_batch(["doc1", "doc2", "doc3"])

    assert result == {
        "doc1": "success",
        "doc2": "failed",
        "doc3": "success"
    }

@pytest.mark.asyncio
async def test_process_speed(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "process_document",
        fake_process_document
    )

    result = await pipeline.process_batch(["slow_doc", "fast_doc"])

    assert list(result.keys()) == ["fast_doc", "slow_doc"]


@pytest.mark.asyncio
async def test_extraction_failure_releases_semaphore(monkeypatch):
    def fake_extract_text(document):
        raise ValueError("Bad document")

    async def fake_download_document(document_id):
        return "fake document"

    monkeypatch.setattr(
        pipeline,
        "extract_text",
        fake_extract_text
    )

    monkeypatch.setattr(
        pipeline,
        "download_document",
        fake_download_document
    )

    monkeypatch.setattr(
        pipeline,
        "save_original",
        fake_original
    )

    test_executor = ThreadPoolExecutor(max_workers=1)

    monkeypatch.setattr(
        pipeline,
        "process_pool",
        test_executor
    )

    test_semaphore = asyncio.Semaphore(1)

    monkeypatch.setattr(
        pipeline,
        "extraction_limit",
        test_semaphore
    )

    with pytest.raises(ValueError):
        await pipeline.process_document("doc1")

    await asyncio.wait_for(
        test_semaphore.acquire(),
        timeout=0.1
    )

    test_semaphore.release()

@pytest.mark.asyncio
async def test_timeout(monkeypatch):
    thread_pool = ThreadPoolExecutor(max_workers=1)
    test_semaphore = asyncio.Semaphore(1)

    monkeypatch.setattr(
        pipeline,
        "extract_text",
        fake_extract
    )

    monkeypatch.setattr(
        pipeline,
        "EXTRACTION_TIMEOUT",
        .05
    )

    monkeypatch.setattr(
        pipeline,
        "process_pool",
        thread_pool
    )

    monkeypatch.setattr(
        pipeline,
        "extraction_limit",
        test_semaphore
    )

    monkeypatch.setattr(
        pipeline,
        "download_document",
        fake_download_document
    )

    monkeypatch.setattr(
        pipeline,
        "save_original",
        fake_original
    )

    with pytest.raises(TimeoutError):
        await pipeline.process_document("doc1")

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(
            test_semaphore.acquire(),
            timeout=.01
        )

    await asyncio.sleep(.2)

    await asyncio.wait_for(
        test_semaphore.acquire(),
        .05
    )

    test_semaphore.release()
    thread_pool.shutdown()


@pytest.mark.asyncio
async def test_executor_failure_releases_semaphore(monkeypatch, caplog):
    test_semaphore = asyncio.Semaphore(1)
    broken_executor = ThreadPoolExecutor(max_workers=1)
    broken_executor.shutdown()

    monkeypatch.setattr(
        pipeline,
        "process_pool",
        broken_executor
    )

    monkeypatch.setattr(
        pipeline,
        "download_document",
        fake_download_document
    )

    monkeypatch.setattr(
        pipeline,
        "save_original",
        fake_original
    )

    monkeypatch.setattr(
        pipeline,
        "extraction_limit",
        test_semaphore
    )

    with pytest.raises(RuntimeError):
        await pipeline.process_document("doc1")

    await asyncio.wait_for(
        test_semaphore.acquire(),
        timeout=.01
    )

    test_semaphore.release()

    assert "Extraction failed for document doc1" in caplog.text
