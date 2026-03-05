from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import repos, docs, chat, export

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AutoDoc AI Backend",
    description="Orchestration layer for the AutoDoc AI project.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router, prefix="/repos", tags=["Repositories"])
app.include_router(docs.router, prefix="/docs", tags=["Documentation"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(export.router, prefix="/export", tags=["Export"])

@app.get("/", tags=["Health"])
async def read_root():
    return {"status": "ok"}
