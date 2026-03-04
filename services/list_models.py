"""
list_models.py
──────────────
Quick utility to list all available models on DigitalOcean Gradient AI.
Run this to find the correct model ID to put in your .env file.

Run:
    python services/list_models.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENDPOINT   = os.getenv("GRADIENT_ENDPOINT_URL", "https://inference.do-ai.run/v1")
ACCESS_KEY = os.getenv("GRADIENT_MODEL_ACCESS_KEY", "")

if not ACCESS_KEY:
    print("❌ GRADIENT_MODEL_ACCESS_KEY not set in .env")
    print("   Get it from: cloud.digitalocean.com → Gradient AI → Serverless Inference → Create Model Access Key")
    exit(1)

client = OpenAI(api_key=ACCESS_KEY, base_url=ENDPOINT)

print(f"\n📡 Fetching models from: {ENDPOINT}\n")
try:
    models = client.models.list()
    model_ids = [m.id for m in models.data]

    print(f"✅ Found {len(model_ids)} available models:\n")

    # Separate code-focused and general models
    code_models = [m for m in model_ids if any(k in m.lower() for k in ["coder", "code", "deepseek", "starcoder"])]
    general_models = [m for m in model_ids if m not in code_models]

    if code_models:
        print("🔧 Code-focused models (recommended for AutoDoc AI):")
        for m in code_models:
            print(f"   → {m}")

    print("\n📚 General models:")
    for m in general_models:
        print(f"   → {m}")

    print(f"\n💡 Recommended: set GRADIENT_MODEL in your .env to one of the code models above")
    print(f"   If no code models listed, use: meta-llama/Meta-Llama-3.1-8B-Instruct")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Check GRADIENT_API_KEY is correct")
    print("   2. Check GRADIENT_ENDPOINT_URL is: https://api.digitalocean.com/v2/gen-ai")
    print("   3. Make sure your DO account has Gradient AI access enabled")
