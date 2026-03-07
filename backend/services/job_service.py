from sqlalchemy.orm import Session
from models import job as models

class JobService:
    def create_job(self, db: Session, repo_url: str) -> models.Job:
        db_job = models.Job(repo_url=repo_url, status=models.JobStatus.PENDING)
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    def get_job(self, db: Session, job_id: str) -> models.Job | None:
        return db.query(models.Job).filter(models.Job.id == job_id).first()

    def update_job_status(self, db: Session, job_id: str, status: models.JobStatus, progress: int | None = None) -> models.Job:
        db_job = self.get_job(db, job_id)
        if db_job:
            db_job.status = status
            if progress is not None:
                db_job.progress = progress
            db.commit()
            db.refresh(db_job)
        return db_job

job_service = JobService()
