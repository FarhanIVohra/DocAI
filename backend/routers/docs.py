from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import doc_schema as schemas
from backend.database import get_db
from backend.services.ai_client import ai_client
from backend.services.job_service import job_service
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
        content = ai_response['content']
        # Skip bleach for diagrams to avoid escaping '>' and other Mermaid symbols
        if request.type in ["architecture", "diagram"]:
            return {"content": content}
            
        sanitized_content = bleach.clean(content)
        return {"content": sanitized_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
