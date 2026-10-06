from fastapi.testclient import TestClient
from api import app
import api
import database
import pytest

client = TestClient(app)

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        db_path
    )
    database.init_db()

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

def test_create_job(test_db):
    job_id = database.create_job("doc1")
    job = database.get_job(job_id)

    assert job[0] == job_id
    assert job[1] == "doc1"
    assert job[2] == "processing"

def test_update_job_status(test_db):
    job_id = database.create_job("doc1")

    database.update_job_status(job_id, "success")

    job = database.get_job(job_id)

    assert job[0] == job_id
    assert job[1] == "doc1"
    assert job[2] == "success"

def test_get_nonexistent_job(test_db):
    row = database.get_job(999)

    assert row is None

def test_job_not_found(test_db):
    response = client.get("/jobs/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}

def test_job_found(test_db):
    job_id = database.create_job("doc1")
    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job_id
    assert data["document_id"] == "doc1"
    assert data["status"] == "processing"