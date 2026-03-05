import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autodoc_v2.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8081/api/ai")
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key")
