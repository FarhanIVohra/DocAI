from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import json
from backend.services.github_service import github_service
from backend.services.ai_client import ai_client

router = APIRouter()

async def process_pr_review(repo_full_name: str, pr_number: int):
    """Background task to fetch diff, review it with AI, and post a comment."""
    diff_text = await github_service.get_pr_diff(repo_full_name, pr_number)
    
    if not diff_text:
        print(f"Failed to get diff for {repo_full_name} #{pr_number}. Skipping review.")
        return
        
    if len(diff_text) > 40000:
        # Avoid enormous diffs blowing up the context window
        diff_text = diff_text[:40000] + "\n\n...[Diff truncated due to size limit]..."
        
    print(f"Triggering AI PR Review for {repo_full_name} #{pr_number}...")
    
    try:
        # Call the AI service specifically for a PR review
        # We will add this specialized endpoint to the AI service next
        ai_response = await ai_client.generate_pr_review(repo_full_name, pr_number, diff_text)
        review_content = ai_response.get("content")
        
        if review_content:
            await github_service.post_pr_comment(repo_full_name, pr_number, review_content)
    except Exception as e:
        print(f"Error during AI PR review: {e}")

@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint for GitHub Webhooks.
    Ensure your webhook is configured for 'Pull request' events.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Check if this is a Pull Request event
    if "pull_request" in payload and "action" in payload:
        action = payload["action"]
        
        # We only care when a PR is opened or new commits are pushed
        if action in ["opened", "synchronize"]:
            repo_full_name = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]
            
            print(f"Webhook received: PR {action} on {repo_full_name} #{pr_number}")
            
            # Offload heavy lifting to background task
            background_tasks.add_task(process_pr_review, repo_full_name, pr_number)
            
            return {"status": "accepted", "message": f"Processing PR review for #{pr_number}"}
            
    return {"status": "ignored", "message": "Not a relevant PR event"}
