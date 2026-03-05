from pydantic import BaseModel
import uuid

class DocGenerateRequest(BaseModel):
    job_id: uuid.UUID
    type: str

class DocGenerateResponse(BaseModel):
    content: str
