from pydantic import BaseModel
import uuid

class ChatMessageRequest(BaseModel):
    job_id: uuid.UUID
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    sources: list[str] | None = None
    timestamp: str
