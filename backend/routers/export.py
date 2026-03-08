from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.export_service import export_service
from backend.services.github_service import github_service
from backend.services.ai_client import ai_client
from backend.services.job_service import job_service
import asyncio

router = APIRouter()

async def get_all_docs(job_id: str, db: Session) -> tuple[dict[str, str], any]:
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    repo_meta = {"repo_url": job.repo_url, "repo_name": "/"}
    
    doc_types = ["readme", "api", "architecture", "changelog", "onboarding", "audit"]
    filenames = ["README.md", "API_DOCS.md", "ARCHITECTURE.md", "CHANGELOG.md", "ONBOARDING.md", "SECURITY_AUDIT.md"]
    
    files = {}
    
    async def fetch_doc(dtype, fname):
        try:
            resp = await ai_client.generate_doc(job_id, dtype, repo_meta)
            if resp and "content" in resp:
                files[fname] = resp["content"]
        except Exception:
            pass # ignore failed docs
            
    tasks = [fetch_doc(dtype, fname) for dtype, fname in zip(doc_types, filenames)]
    await asyncio.gather(*tasks)
    
    if not files:
        raise HTTPException(status_code=404, detail="No documentation found.")
        
    return files, job

@router.get("/md/{job_id}")
async def export_markdown(job_id: str, db: Session = Depends(get_db)):
    try:
        files, _ = await get_all_docs(job_id, db)
        zip_bytes = export_service.create_markdown_zip(files)
        return Response(content=zip_bytes, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=docs_{job_id}.zip"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

@router.get("/pdf/{job_id}")
async def export_pdf(job_id: str, db: Session = Depends(get_db)):
    try:
        files, _ = await get_all_docs(job_id, db)
        pdf_bytes = export_service.create_markdown_pdf(files)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=docs_{job_id}.pdf"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")

@router.post("/pr/{job_id}")
async def create_gist_export(job_id: str, db: Session = Depends(get_db)):
    try:
        files, job = await get_all_docs(job_id, db)
        gist_url = await github_service.create_gist(files, f"AutoDoc AI generated documentation for {job.repo_url}")
        
        if not gist_url:
            import json
            # Fallback for when the GITHUB_TOKEN doesn't have gist permissions
            return {"fallback_data": json.dumps(files)}
            
        return {"pr_url": gist_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")
