from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from services.export_service import export_service
from services.ai_client import ai_client

router = APIRouter()

@router.get("/md/{job_id}")
async def export_markdown(job_id: str, db: Session = Depends(get_db)):
    # In a real app, you would fetch all doc types for the job
    # For now, we'll just get the README
    try:
        readme = await ai_client.generate_doc(job_id, "readme")
        files = {"README.md": readme['content']}
        zip_bytes = export_service.create_markdown_zip(files)
        return Response(content=zip_bytes, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=docs_{job_id}.zip"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")



@router.post("/pr/{job_id}")
async def create_pr(job_id: str, db: Session = Depends(get_db)):
    # This would involve GitHub OAuth and using the GitHub API
    # to create a pull request. This is a complex flow.
    return {"pr_url": "https://github.com/user/repo/pull/123"} # Placeholder
