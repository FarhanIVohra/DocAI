from celery import Celery
from config import REDIS_URL

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery_app.task
def process_repo(repo_url: str):
    # This is where you would trigger the AI indexing
    # and monitor its progress.
    print(f"Processing repository: {repo_url}")
    return {"status": "complete"}
