import httpx
import os
from typing import Optional

# GitHub App/PAT authentication
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitHubService:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else ""
        }

    async def get_pr_diff(self, repo_full_name: str, pr_number: int) -> Optional[str]:
        """Fetch the raw diff of a pull request."""
        url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
        # Request diff format
        diff_headers = self.headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=diff_headers)
            if resp.status_code == 200:
                print(f"DEBUG: Successfully fetched diff for {repo_full_name} PR #{pr_number}")
                return resp.text
            else:
                print(f"ERROR: Failed to fetch diff: {resp.status_code} - {resp.text}")
                return None

    async def post_pr_comment(self, repo_full_name: str, pr_number: int, comment_body: str) -> bool:
        """Post a comment to a specific PR."""
        if not GITHUB_TOKEN:
            print("WARNING: GITHUB_TOKEN not set, cannot post comment. Logging instead:")
            print(f"\n--- PR COMMENT ({repo_full_name} #{pr_number}) ---\n{comment_body}\n--- END COMMENT ---\n")
            return True

        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, 
                headers=self.headers, 
                json={"body": comment_body}
            )
            if resp.status_code == 201:
                print(f"DEBUG: Successfully posted comment to {repo_full_name} PR #{pr_number}")
                return True
            else:
                print(f"ERROR: Failed to post comment: {resp.status_code} - {resp.text}")
                return False

github_service = GitHubService()
