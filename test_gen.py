import httpx
import asyncio

async def test_gen():
    job_id = "df96deb3-4e01-4c8b-8156-15bfb4d7faec" # we know this one from logs
    async with httpx.AsyncClient(timeout=30) as client:
        print("Testing backend...")
        try:
            resp = await client.post("http://127.0.0.1:8000/docs/generate", json={"job_id": job_id, "type": "api"})
            print(f"Backend Status: {resp.status_code}")
            print(f"Backend Response: {resp.text}")
        except Exception as e:
            print(f"Backend Error: {e}")
            
        print("Testing AI service direct...")
        try:
            resp = await client.post("http://127.0.0.1:8001/api/ai/generate", json={"job_id": job_id, "type": "api", "repo_meta": {}})
            print(f"AI Service Status: {resp.status_code}")
            # print(f"AI Service Response: {resp.text}")
        except Exception as e:
            print(f"AI Service Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gen())
