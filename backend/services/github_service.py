from github import Github
from config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

class GitHubService:
    def __init__(self, access_token: str | None = None):
        self.g = Github(access_token)

    def get_auth_url(self):
        return f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo"

    # In a real app, you would exchange the code for an access token

    def create_pr(self, repo_full_name: str, title: str, body: str, head: str, base: str):
        repo = self.g.get_repo(repo_full_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return pr.html_url

github_service = GitHubService()
