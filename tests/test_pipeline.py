import pytest
import pipeline

async def fake_process_document(document_id):
    if document_id == "doc2":
        raise Exception("Processing failed")

@pytest.mark.asyncio
async def test_process_batch_all_success(monkeypatch):
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