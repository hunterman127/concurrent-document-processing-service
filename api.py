from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline import process_document
from database import get_job, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def status():
    return {"status": "ok"}

class ProcessDocumentRequest(BaseModel):
    document_id: str 

class ProcessDocumentResponse(BaseModel):
    document_id: str
    status: str

@app.post("/documents/process", response_model=ProcessDocumentResponse)
async def post_request(request: ProcessDocumentRequest):
    try:    
        await process_document(request.document_id)
    
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Document processing timed out"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document processing failed"
        )

    else:
        return {
                "document_id": request.document_id,
                "status": "success"
                }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: int):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    job_info = {
        "job_id": job[0],
        "document_id": job[1],
        "status": job[2],
        "created_at": job[3]
    }

    return job_info
