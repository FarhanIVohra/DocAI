import sqlite3
import httpx
import asyncio

async def verify():
    # Get a job ID from backend DB
    conn = sqlite3.connect('autodoc_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("No jobs in v2 db")
        return
        
    job_id = row[0]
    print(f"Testing with job_id: {job_id}")
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post("http://127.0.0.1:8000/docs/generate", json={"job_id": job_id, "type": "api"})
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print("SUCCESS: 500 error resolved.")
            else:
                print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
