from sqlalchemy import Column, String, Enum, Integer
import uuid
from database import Base
import enum

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)
