# Concurrent Document Processing Service

## Overview

The Concurrent Document Processing Service is a Python backend service that processes documents while tracking each processing job in a persistent SQLite database. The service uses asynchronous orchestration to coordinate document downloads, backups, CPU-intensive text extraction, and storage while allowing independent operations to make progress concurrently.

FastAPI exposes HTTP endpoints for submitting documents for processing, checking service health, and retrieving job status. The application is containerized with Docker and supports persistent database storage through Docker volumes.

## Architecture

The document-processing pipeline follows this general flow:

```text
                    Download Document
                           |
              +------------+------------+
              |                         |
              v                         v
       Backup Original            Extract Text
       Blocking I/O               CPU Intensive
          Thread                   Process Pool
              |                         |
              |                   Semaphore Limit
              |                         |
              |                         v
              |                    Store Text
              |                         |
              +------------+------------+
                           |
                           v
                   Update Job Status
```

The service uses different concurrency mechanisms based on the type of work being performed:

- **asyncio** coordinates asynchronous operations and allows independent work to make progress without blocking the event loop.
- **Threads** handle blocking synchronous I/O, such as the legacy document backup operation.
- **Processes** handle CPU-intensive text extraction so CPU-bound Python work does not block the main event loop and can execute in separate Python processes.
- **Semaphores** limit simultaneous extraction jobs so document-processing requests cannot consume the entire process pool.

## Features

- Concurrent document-processing pipeline
- Asynchronous request orchestration with `asyncio`
- Blocking I/O execution using threads
- CPU-intensive extraction using a shared process pool
- Configurable extraction concurrency limits
- Processing timeouts
- Cancellation-safe resource cleanup
- Batch processing with failure isolation
- Persistent job-status tracking with SQLite
- Structured application logging
- Environment-based configuration
- REST API built with FastAPI and Pydantic
- Automatic database initialization during application startup
- Automated testing with pytest
- Docker containerization
- Persistent SQLite storage using Docker volumes

## API Endpoints

### `GET /health`

Checks whether the API is running.

Example response:

```json
{
  "status": "ok"
}
```

### `POST /documents/process`

Submits a document for processing.

Example request:

```json
{
  "document_id": "document-123"
}
```

Example successful response:

```json
{
  "document_id": "document-123",
  "status": "success"
}
```

The endpoint returns an HTTP `504` response if processing exceeds the configured timeout and an HTTP `500` response if processing fails for another reason.

### `GET /jobs/{job_id}`

Retrieves the persisted status of a processing job.

Example response:

```json
{
  "job_id": 1,
  "document_id": "document-123",
  "status": "success",
  "created_at": "2026-10-06T20:00:00+00:00"
}
```

A nonexistent job returns HTTP `404`.

## Configuration

Configuration is loaded from environment variables. Local development can use a `.env` file.

| Variable | Default | Purpose |
| --- | --- | --- |
| `EXTRACTION_TIMEOUT` | `10` | Maximum time in seconds allowed for extraction and text storage |
| `EXTRACTION_CONCURRENCY` | `3` | Maximum number of simultaneous document extractions |
| `PROCESS_POOL_WORKERS` | `8` | Number of workers available in the shared process pool |
| `DB_PATH` | `documents.db` | Location of the SQLite database |

An example configuration is provided in `.env.example`.

## Running Locally

Create a virtual environment:

```powershell
python -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --reload
```

The API will be available on port `8000`.

FastAPI's interactive Swagger documentation is available at `/docs`.

## Running with Docker

Build the Docker image:

```powershell
docker build -t document-processing-service .
```

Create a persistent Docker volume:

```powershell
docker volume create document-data
```

Run the application:

```powershell
docker run --name document-api -p 8000:8000 -e DB_PATH=/data/documents.db -v document-data:/data document-processing-service
```

The `document-data` volume stores the SQLite database outside the container's writable filesystem. This allows job data to survive container deletion and replacement.

## Testing

Run the complete test suite with:

```powershell
python -m pytest tests -v
```

The test suite covers API behavior, request validation, database operations, batch processing, timeout behavior, extraction failures, semaphore cleanup, and executor failures.

## Engineering Decisions

### Threads vs. Processes

The service distinguishes between I/O-bound and CPU-bound operations.

The legacy backup operation is synchronous and blocking, so it is moved to a worker thread rather than blocking the asyncio event loop.

Text extraction is CPU-intensive and therefore runs in a `ProcessPoolExecutor`. Separate processes allow CPU-bound Python work to execute outside the main Python interpreter rather than blocking the event loop.

### Extraction Concurrency

The process pool can also support other CPU workloads, so document extraction should not consume every available process worker. A semaphore limits the number of document extractions that can run simultaneously.

The semaphore represents the lifetime of the actual extraction operation rather than only the lifetime of the HTTP request.

### Timeout and Cancellation Cleanup

Document extraction and text storage have a configurable timeout. Timing out an asynchronous request does not necessarily stop CPU work that has already started in another process.

The service protects the underlying extraction future from cancellation and performs background cleanup when necessary. The extraction semaphore is released only when the underlying extraction operation has actually finished.

### Failure Isolation

Batch processing starts multiple document-processing tasks concurrently. A failure in one document does not automatically cancel the remaining documents.

Each result is associated with its original document ID so the caller can determine which documents succeeded or failed.

### Persistent Job Tracking

Each processing attempt creates a job record in SQLite. Job state is updated as processing succeeds or fails, allowing processing status to survive beyond the lifetime of an individual request.

Database connections use deterministic cleanup, and database initialization runs automatically during the FastAPI application startup lifecycle.

### Docker Persistence

Containers are treated as disposable application instances. Persistent database state is kept outside the container filesystem using a Docker volume.

This allows the application container to be rebuilt, deleted, or replaced without deleting previously stored job records.