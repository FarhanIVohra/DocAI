from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import repo_schema as schemas
from backend.database import get_db
from backend.services.job_service import job_service
from backend.services.ai_client import ai_client

router = APIRouter()

@router.post("/submit", response_model=schemas.RepoSubmitResponse)
async def submit_repo(request: schemas.RepoSubmitRequest, db: Session = Depends(get_db)):
    try:
        job = job_service.create_job(db, str(request.repo_url))
        ai_response = await ai_client.index_repo(str(request.repo_url), job_id=str(job.id))
        job_service.update_job_status(db, job.id, "processing")
        return {"job_id": job.id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        # If job was created, we can try to mark it as failed
        # But if create_job itself failed, 'job' is not defined
        print(f"ERROR in submit_repo: {e}")
        raise HTTPException(status_code=500, detail=f"Submission error: {e}")

@router.get("/status/{job_id}", response_model=schemas.JobStatusResponse)
async def get_status(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Sync status from AI service if it's not ready yet
    if job.status in [schemas.JobStatus.PENDING, schemas.JobStatus.PROCESSING]:
        try:
            ai_status = await ai_client.get_status(job_id)
            if ai_status:
                # Map AI status to backend JobStatus
                new_status = schemas.JobStatus.PROCESSING
                if ai_status.get("status") == "ready":
                    new_status = schemas.JobStatus.READY
                elif ai_status.get("status") == "failed":
                    new_status = schemas.JobStatus.FAILED
                
                job = job_service.update_job_status(
                    db, 
                    job_id, 
                    status=new_status, 
                    progress=ai_status.get("progress", 0)
                )
        except Exception as e:
            print(f"DEBUG: Failed to sync status for {job_id}: {e}")
            
    return {"job_id": job.id, "status": job.status, "progress": job.progress}
