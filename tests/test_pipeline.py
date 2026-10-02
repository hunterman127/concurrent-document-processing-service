import asyncio
import pytest
import pipeline

async def fake_process_document(document_id):
    if document_id == "slow_doc":
        await asyncio.sleep(0.05)

    if document_id == "doc2":
        raise Exception("Failed")

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
    