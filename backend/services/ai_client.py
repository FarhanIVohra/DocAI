import httpx
from backend.config import AI_SERVICE_URL

class AIClient:
    def __init__(self):
        self.base_url = AI_SERVICE_URL

    async def index_repo(self, repo_url: str, job_id: str | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/index-repo", json={"repo_url": repo_url, "job_id": job_id})
            response.raise_for_status()
            return response.json()

    async def get_status(self, job_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/status/{job_id}")
            response.raise_for_status()
            return response.json()

    async def generate_doc(self, job_id: str, doc_type: str, repo_meta: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/generate", json={"job_id": job_id, "type": doc_type, "repo_meta": repo_meta}, timeout=300.0)
            response.raise_for_status()
            return response.json()

    async def chat(self, job_id: str, message: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/chat", json={"job_id": job_id, "message": message}, timeout=300.0)
            response.raise_for_status()
            return response.json()

    async def generate_pr_review(self, repo_full_name: str, pr_number: int, diff_text: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate-pr-review", 
                json={
                    "repo_full_name": repo_full_name, 
                    "pr_number": pr_number, 
                    "diff_text": diff_text
                }, 
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()

ai_client = AIClient()
