from pydantic import BaseModel, HttpUrl
import uuid
from models.job import JobStatus

class RepoSubmitRequest(BaseModel):
    repo_url: HttpUrl

class RepoSubmitResponse(BaseModel):
    job_id: uuid.UUID

class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    progress: int | None = None
