from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import doc_schema as schemas
from database import get_db
from services.ai_client import ai_client
from services import job_service
import bleach

router = APIRouter()

@router.post("/generate", response_model=schemas.DocGenerateResponse)
async def generate_doc(request: schemas.DocGenerateRequest, db: Session = Depends(get_db)):
    try:
        job = job_service.get_job(db, str(request.job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        repo_meta = {
            "repo_url": job.repo_url,
            "repo_name": "/",
        }
        
        ai_response = await ai_client.generate_doc(str(request.job_id), request.type, repo_meta)
        sanitized_content = bleach.clean(ai_response['content'])
        return {"content": sanitized_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
