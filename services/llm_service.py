"""
llm_service.py
──────────────
Wrapper for DigitalOcean Gradient AI Serverless Inference API.
The API is fully OpenAI-compatible — uses the `openai` Python SDK
pointed at DO's base URL.

Usage:
    from services.llm_service import get_llm
    llm = get_llm()
    result = llm.generate_with_prompt("readme", "def add(a,b): return a+b")
"""

import os
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError

load_dotenv()

# ─── Config ──────────────────────────────────────────────────────────────────
# ─── Config ──────────────────────────────────────────────────────────────────
GRADIENT_ENDPOINT_URL  = os.getenv("GRADIENT_ENDPOINT_URL", "https://inference.do-ai.run/v1")
GRADIENT_MODEL_ACCESS_KEY = os.getenv("GRADIENT_MODEL_ACCESS_KEY", "")  # NOT your DO personal key
GRADIENT_MODEL         = os.getenv("GRADIENT_MODEL", "deepseek-ai/DeepSeek-R1")


DEFAULT_MAX_TOKENS  = 1024
DEFAULT_TEMPERATURE = 0.2    # Low = more deterministic, better for docs
TIMEOUT_SECONDS     = 120
MAX_RETRIES         = 3
RETRY_DELAY         = 2.0

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(prompt_name: str) -> str:
    """Load a system prompt from the prompts/ directory."""
    path = PROMPTS_DIR / f"{prompt_name}_prompt.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


class GradientLLM:
    """
    DigitalOcean Gradient AI client using OpenAI-compatible SDK.

    Falls back to a mock response if GRADIENT_API_KEY is not set,
    so local development works without any credentials.
    """

    def __init__(self):
        self.model = GRADIENT_MODEL
        self._is_mock = not bool(GRADIENT_MODEL_ACCESS_KEY)

        if self._is_mock:
            print("⚠️  GRADIENT_MODEL_ACCESS_KEY not set — using mock responses.")
            print("   DON'T use your personal API key — create a Model Access Key:")
            print("   cloud.digitalocean.com → Gradient AI → Serverless Inference → Create Model Access Key")
            return

        # OpenAI SDK pointed at DO's Gradient AI inference endpoint
        self.client = OpenAI(
            api_key=GRADIENT_MODEL_ACCESS_KEY,
            base_url=GRADIENT_ENDPOINT_URL,
            timeout=TIMEOUT_SECONDS,
            max_retries=0,
        )
        print(f"✅ GradientLLM ready — model: {self.model}")

    def _mock_response(self, user_message: str) -> str:
        first_60 = user_message[:60].replace("\n", " ")
        return (
            f"**[MOCK — set GRADIENT_API_KEY to enable real responses]**\n\n"
            f"Received input: `{first_60}...`\n\n"
            "This is a placeholder. Once your .env is configured with a valid\n"
            "DigitalOcean API key and GRADIENT_ENDPOINT_URL, real documentation\n"
            "will be generated here."
        )

    def generate(
        self,
        user_message: str,
        system_prompt: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """
        Generate a completion from Gradient AI.

        Args:
            user_message: The code / question to process
            system_prompt: Optional system instructions
            max_tokens: Token limit for response
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Generated text string
        """
        if self._is_mock:
            return self._mock_response(user_message)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content

            except APITimeoutError:
                print(f"  ⏱️  Timeout (attempt {attempt}/{MAX_RETRIES})")
                last_error = "Timeout"
            except APIError as e:
                print(f"  ❌ API error: {e.status_code} — {e.message}")
                if e.status_code in (400, 401, 403):
                    raise  # Not retryable
                last_error = str(e)
            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                last_error = str(e)

            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                print(f"  🔄 Retrying in {wait:.0f}s...")
                time.sleep(wait)

        raise RuntimeError(f"Gradient AI failed after {MAX_RETRIES} attempts: {last_error}")

    def generate_with_prompt(
        self,
        prompt_name: str,
        user_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """
        Generate using a named prompt from the prompts/ directory.

        Args:
            prompt_name: readme | api_doc | diagram | changelog | onboarding | chat
            user_message: The code/question to process

        Returns:
            Generated documentation string
        """
        system_prompt = load_prompt(prompt_name)
        return self.generate(user_message, system_prompt, max_tokens)

    def list_available_models(self) -> list[str]:
        """Fetch all available models from Gradient AI endpoint."""
        if self._is_mock:
            return ["[mock mode — no real models available]"]
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            print(f"  ❌ Could not fetch models: {e}")
            return []


# ─── Singleton ────────────────────────────────────────────────────────────────
_llm_instance: Optional[GradientLLM] = None


def get_llm() -> GradientLLM:
    """Get or create the singleton GradientLLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = GradientLLM()
    return _llm_instance
