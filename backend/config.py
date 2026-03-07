import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autodoc_v2.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
AI_HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1")
AI_PORT = os.getenv("AI_SERVICE_PORT", "8081")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", f"http://{AI_HOST}:{AI_PORT}/api/ai")
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key")
