import httpx
import asyncio
import json

async def test_live_pr():
    # A mock payload simulating a "pull_request.opened" event
    # specifically for the PR the user just created.
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 4
        },
        "repository": {
            "full_name": "FarhanIVohra/DocAI"
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print(f"Injecting mock webhook for FarhanIVohra/DocAI PR #1 directly into local backend...")
        try:
            resp = await client.post("http://127.0.0.1:8000/github/webhook", json=payload)
            print(f"Backend Status: {resp.status_code}")
            print(f"Backend Response: {resp.json()}")
            print("\nWaiting for background AI generation to complete (approx 30s)...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_pr())
