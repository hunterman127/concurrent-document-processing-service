from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import process_document

app = FastAPI()

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
    