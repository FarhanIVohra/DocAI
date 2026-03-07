from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship
import uuid
from database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    job_id = Column(String(36), ForeignKey("jobs.id"))

    user = relationship("User")
    job = relationship("Job")
