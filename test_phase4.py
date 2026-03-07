import httpx
import time
import asyncio
import sqlite3
import json

async def test_parallel_gen():
    base_url = "http://127.0.0.1:8000"
    repo_url = "https://github.com/fastapi/fastapi"
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        # 1. Submit repo
        print(f"Submitting {repo_url}...")
        resp = await client.post(f"{base_url}/repos/submit", json={"repo_url": repo_url})
        job_id = resp.json()["job_id"]
        print(f"Job ID: {job_id}")
        
        # 2. Poll for Status
        print("Polling for status...")
        while True:
            status_resp = await client.get(f"{base_url}/repos/status/{job_id}")
            status_data = status_resp.json()
            print(f"Status: {status_data['status']} ({status_data['progress']}%)")
            if status_data["status"] == "ready":
                break
            if status_data["status"] == "failed":
                print("Job failed!")
                return
            await asyncio.sleep(5)
            
        print("Indexing ready. Waiting 10 seconds for background pre-generation...")
        await asyncio.sleep(10)
        
        # 3. Check DB directly for cache
        conn = sqlite3.connect("ai_service_v3.db")
        cursor = conn.cursor()
        cursor.execute("SELECT docs_json FROM ai_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if row and row[0]:
            docs = json.loads(row[0])
            print(f"Cached docs found in DB: {list(docs.keys())}")
        else:
            print("No cached docs found in DB yet.")
        conn.close()
        
        # 4. Test generate endpoint speed
        types = ["readme", "api", "architecture"]
        for t in types:
            start_time = time.time()
            gen_resp = await client.get(f"http://localhost:8000/docs/generate?jobId={job_id}&type={t}")
            end_time = time.time()
            print(f"Generated {t} in {end_time - start_time:.2f}s")
            # If it's cached, it should be < 1s
            if end_time - start_time < 2.0:
                print(f"SUCCESS: {t} was served from cache!")
            else:
                print(f"FAIL: {t} was NOT served from cache (took {end_time - start_time:.2f}s)")

if __name__ == "__main__":
    asyncio.run(test_parallel_gen())
