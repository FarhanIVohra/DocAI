import httpx
import asyncio
import json

async def test_webhook():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 12822  # A known FastAPI PR
        },
        "repository": {
            "full_name": "fastapi/fastapi"
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("Sending mock PR opened webhook...")
        try:
            resp = await client.post("http://127.0.0.1:8000/github/webhook", json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
            print("\nCheck backend_p4.log and ai_service_p4.log for background processing progress.")
            print("\nWait about 30 seconds for the AI to fetch the diff and generate the review.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
