from pydantic import BaseModel
import uuid

class ChatMessageRequest(BaseModel):
    job_id: uuid.UUID
    message: str

class ChatMessageResponse(BaseModel):
    answer: str
    sources: list[str] | None = None
