import httpx
import asyncio

async def test_submit():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://127.0.0.1:8000/repos/submit", json={"repo_url": "https://github.com/fastapi/fastapi"})
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_submit())
