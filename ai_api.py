from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os

app = FastAPI(title="AutoDoc AI - AI Service API")

# Simple in-memory status store for demonstration
# In a real app, use Redis or a database
job_status = {}

@app.get("/")
async def root_health():
    return {"status": "ok", "message": "AutoDoc AI Service is running"}

@app.get("/api/ai/health")
async def health_check():
    return {"status": "ok", "service": "AI Microservice"}

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

def background_index(repo_url: str, job_id: str):
    try:
        def update_status(progress):
            current = job_status.get(job_id, {})
            job_status[job_id] = {
                "status": "processing", 
                "progress": progress,
                "repo_url": current.get("repo_url"),
                "repo_name": current.get("repo_name")
            }
            print(f"DEBUG: Job {job_id} progress updated to {progress}%")

        update_status(5)
        indexer = get_indexer()
        update_status(10)
        
        # Clone repo manually to show progress
        repo_path = indexer._clone_repo(repo_url, job_id)
        update_status(20)
        
        # Use index_local_path with progress callback
        indexer.index_local_path(repo_path, job_id, repo_url=repo_url, update_status_callback=update_status)
        
        current = job_status.get(job_id, {})
        job_status[job_id] = {
            "status": "ready", 
            "progress": 100,
            "repo_url": current.get("repo_url", repo_url),
            "repo_name": current.get("repo_name", repo_url.split("/")[-1])
        }
        print(f"DEBUG: Job {job_id} indexing complete.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Indexing failed for {job_id}: {e}")
        job_status[job_id] = {"status": "failed", "error": str(e)}

@app.post("/api/ai/index-repo")
async def index_repo(request: RepoSubmitRequest, background_tasks: BackgroundTasks):
    job_id = request.job_id or str(uuid.uuid4())
    
    # Extract a simple name from the URL
    repo_name = request.repo_url.split("/")[-1].replace(".git", "")
    
    job_status[job_id] = {
        "status": "pending", 
        "progress": 0,
        "repo_url": request.repo_url,
        "repo_name": repo_name
    }
    background_tasks.add_task(background_index, request.repo_url, job_id)
    return {"job_id": job_id}

@app.get("/api/ai/status/{job_id}")
async def get_status(job_id: str):
    if job_id in job_status:
        return job_status[job_id]
    
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
        # Map frontend doc types to generator types
        doc_type_map = {
            "readme": "readme",
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
            
        # Prioritize repo_meta from request, fallback to indexer (mock)
        repo_meta = request.repo_meta or get_indexer().get_repo_meta(request.job_id)
        generator = get_generator()
        
        print(f"DEBUG: Generating {target_type} for job {request.job_id} using metadata: {repo_meta}")
        content = generator.generate(target_type, request.job_id, repo_meta)
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        print(f"ERROR during generation: {err_trace}")
        raise HTTPException(status_code=500, detail=f"AI Generation Error: {str(e)}\n{err_trace}")

@app.post("/api/ai/chat")
async def chat(request: ChatMessageRequest):
    try:
        # Check if indexing is in progress or not started
        if request.job_id not in job_status:
             # Fallback: if job not in status, check if collection exists in Chroma
             print(f"DEBUG: Job {request.job_id} not in memory, attempting to initialize ChatAgent anyway.")
             
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
    uvicorn.run(app, host="0.0.0.0", port=8081)
