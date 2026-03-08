from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="AutoDoc AI - AI Service API")

from ai_database import engine, Base, AIJob, SessionLocal, init_db

# Initialize DB on startup
init_db()

# Replaces in-memory job_status = {}
def update_job_db(job_id: str, status: str = None, progress: int = None, error: str = None, metadata: dict = None, docs: dict = None):
    db = SessionLocal()
    try:
        job = db.query(AIJob).filter(AIJob.job_id == job_id).first()
        if not job:
            job = AIJob(job_id=job_id)
            db.add(job)
        if status: job.status = status
        if progress is not None: job.progress = progress
        if error: job.error = error
        if metadata: job.metadata_json = metadata
        if docs:
            existing_docs = job.docs_json or {}
            existing_docs.update(docs)
            job.docs_json = existing_docs
        db.commit()
    finally:
        db.close()

def get_job_db(job_id: str):
    db = SessionLocal()
    try:
        return db.query(AIJob).filter(AIJob.job_id == job_id).first()
    finally:
        db.close()


class RepoSubmitRequest(BaseModel):
    repo_url: str
    job_id: Optional[str] = None

class DocGenerateRequest(BaseModel):
    job_id: str
    type: str
    repo_meta: Optional[dict] = None

class ChatMessageRequest(BaseModel):
    job_id: str
    message: str

class PRReviewRequest(BaseModel):
    repo_full_name: str
    pr_number: int
    diff_text: str

_indexer = None
_generator = None

def get_indexer():
    global _indexer
    if _indexer is None:
        from services.repo_indexer import RepoIndexer
        _indexer = RepoIndexer()
    return _indexer

def get_generator():
    global _generator
    if _generator is None:
        from services.doc_generator import DocGenerator
        _generator = DocGenerator()
    return _generator

# Simple chat session cache: job_id -> ChatAgent
chat_sessions = {}

async def background_generate_all(job_id: str, repo_meta: dict):
    """Pre-generate all document types in parallel after indexing."""
    print(f"DEBUG: Starting parallel generation for {job_id}...")
    generator = get_generator()
    
    # List of types we want to pre-generate
    types = ["readme", "api-docs", "diagram"]
    
    for t in types:
        try:
            print(f"DEBUG: Pre-generating {t} for {job_id}...")
            content = generator.generate(t, job_id, repo_meta)
            update_job_db(job_id, docs={t: content})
        except Exception as e:
            print(f"ERROR: Pre-generation failed for {t}: {e}")

def background_index(repo_url: str, job_id: str, background_tasks: BackgroundTasks):
    try:
        def update_status(progress):
            update_job_db(job_id, status="processing", progress=progress)
            print(f"DEBUG: Job {job_id} progress updated to {progress}%")

        update_status(5)
        indexer = get_indexer()
        update_status(10)
        
        # Clone repo manually to show progress
        repo_path = indexer._clone_repo(repo_url, job_id)
        update_status(20)
        
        # Use index_local_path with progress callback
        result = indexer.index_local_path(repo_path, job_id, repo_url=repo_url, update_status_callback=update_status)
        
        update_job_db(job_id, status="ready", progress=100, metadata=result)
        print(f"DEBUG: Job {job_id} indexing complete. Triggering pre-generation...")
        
        # Trigger parallel generation
        background_tasks.add_task(background_generate_all, job_id, result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Indexing failed for {job_id}: {e}")
        update_job_db(job_id, status="failed", error=str(e))


@app.post("/api/ai/index-repo")
async def index_repo(request: RepoSubmitRequest, background_tasks: BackgroundTasks):
    job_id = request.job_id or str(uuid.uuid4())
    update_job_db(job_id, status="pending", progress=0)
    background_tasks.add_task(background_index, request.repo_url, job_id, background_tasks)
    return {"job_id": job_id}


@app.get("/api/ai/status/{job_id}")
async def get_status(job_id: str):
    job = get_job_db(job_id)
    if job:
        return {"status": job.status, "progress": job.progress, "error": job.error}

    
    # Check if collection exists in ChromaDB (persistence check)
    try:
        indexer = get_indexer()
        collection_name = f"repo_{job_id}"
        # This will raise an error if it doesn't exist
        indexer.embedder.chroma_client.get_collection(
            name=collection_name,
            embedding_function=indexer.embedder.embedding_fn
        )
        return {"status": "ready", "progress": 100}
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/ai/generate")
async def generate_doc(request: DocGenerateRequest):
    try:
        doc_type_map = {
            "readme": "readme",
            "api": "api-docs",
            "api-docs": "api-docs",
            "architecture": "diagram",
            "diagram": "diagram",
            "changelog": "changelog",
            "onboarding": "onboarding",
            "audit": "audit",
            "security-audit": "audit",
            "code-review": "code-review"
        }
        
        target_type = doc_type_map.get(request.type)
        if not target_type:
            raise HTTPException(status_code=400, detail=f"Unsupported doc type: {request.type}")
            
        # Fetch metadata and cached docs from DB
        job = get_job_db(request.job_id)
        
        # Check for cached content first
        if job and job.docs_json and target_type in job.docs_json:
            print(f"DEBUG: Serving cached {target_type} for {request.job_id}")
            return {"content": job.docs_json[target_type]}

        # If not cached, generate on the fly
        if not job or not job.metadata_json:
            print(f"DEBUG: Job {request.job_id} missing metadata or not in DB. Falling back to indexer metadata.")
            # Fallback for old jobs not in v3 DB
            repo_meta = get_indexer().get_repo_meta(request.job_id)
        else:
            repo_meta = job.metadata_json
            
        generator = get_generator()
        
        print(f"DEBUG: Cached {target_type} not found, generating on the fly...")
        content = generator.generate(target_type, request.job_id, repo_meta)
        
        # Save to cache for next time
        update_job_db(request.job_id, docs={target_type: content})
        
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate-pr-review")
async def generate_pr_review(request: PRReviewRequest):
    try:
        from services.llm_service import get_llm
        from pathlib import Path
        
        prompt_path = Path(__file__).parent / "prompts" / "pr_review_prompt.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "You are a code reviewer."
        
        user_message = (
            f"Repository: {request.repo_full_name}\n"
            f"Pull Request: #{request.pr_number}\n\n"
            f"Diff:\n{request.diff_text}"
        )
        
        llm = get_llm()
        content = llm.generate(user_message, system_prompt, max_tokens=1000)
        
        return {"content": content}
    except Exception as e:
        import traceback
        import sys
        # Print safely to avoid charmap codec errors on Windows
        try:
            print(f"Error in generate_pr_review: {e}")
            sys.stderr.buffer.write(traceback.format_exc().encode('utf-8'))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/chat")
async def chat(request: ChatMessageRequest):
    try:
        # Check if indexing is in progress or not started
        job = get_job_db(request.job_id)
        if not job:
             # Fallback: if job not in status, check if collection exists in Chroma
             print(f"DEBUG: Job {request.job_id} not in DB, attempting to initialize ChatAgent anyway.")
             
        if request.job_id not in chat_sessions:
            from services.chat_agent import ChatAgent
            chat_sessions[request.job_id] = ChatAgent(request.job_id)
            
        agent = chat_sessions[request.job_id]

        result = agent.chat(request.message)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Provide a more helpful error message
        error_msg = str(e)
        if "Collection" in error_msg and "not found" in error_msg:
             return {
                 "answer": "I'm still analyzing the repository. Please wait a few more seconds for the initial indexing to complete.",
                 "sources": [],
                 "turn": 0,
                 "indexing_in_progress": True
             }
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AI_SERVICE_PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)

