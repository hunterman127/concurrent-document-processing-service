from fastapi.testclient import TestClient
from api import app
import api

client = TestClient(app)

def test_healthy_get_request():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

async def fake_process_document(document_id):
    pass

def test_healthy_post_request(monkeypatch):
    monkeypatch.setattr(
        api,
        "process_document",
        fake_process_document
    )

    response = client.post("/documents/process", json={"document_id": "doc123"})
    assert response.status_code == 200
    assert response.json() == {
                                "document_id": "doc123",
                                "status": "success"
                                }

async def fake_timeout(document_id):
    raise TimeoutError

def test_timeout(monkeypatch):
    monkeypatch.setattr(
        api,
        "process_document",
        fake_timeout
    )
    response = client.post("/documents/process", json={"document_id": "doc123"})
    assert response.status_code == 504
    assert response.json() == {
                                "detail": "Document processing timed out"
                                }


async def fake_failure(document_id):
    raise RuntimeError("something broke")

def test_processing_failure(monkeypatch):
    monkeypatch.setattr(
        api,
        "process_document",
        fake_failure
    )

    response = client.post("/documents/process", json={"document_id": "doc123"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Document processing failed"}

async def fake_should_not_run(document_id):
    raise AssertionError("Pipeline should not have been called")

def test_invalid_request():
    response = client.post(
        "/documents/process",
        json={"wrong_field": "doc123"}
    )

    assert response.status_code == 422