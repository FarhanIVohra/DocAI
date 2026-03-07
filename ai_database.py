from sqlalchemy import create_engine, Column, String, Integer, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./ai_service_v3.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AIJob(Base):
    __tablename__ = "ai_jobs"

    job_id = Column(String, primary_key=True, index=True)
    repo_url = Column(String)
    status = Column(String, default="pending")
    progress = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    docs_json = Column(JSON, nullable=True) # Map of doc_type -> content

def init_db():
    Base.metadata.create_all(bind=engine)

def get_ai_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
