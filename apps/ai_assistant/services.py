import os
import time
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_PATHS = [BASE_DIR / ".env", Path.cwd() / ".env"]
for dotenv_path in DOTENV_PATHS:
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)


class GeminiService:
    def __init__(self):
        # Lazy import to avoid loading heavy crypto deps during app startup/migrations.
        # (On some Windows setups, native deps can fail to load under deep paths.)
        from google import genai

        api_key = None
        try:
            from django.conf import settings
            api_key = getattr(settings, "GEMINI_API_KEY", None)
        except Exception:
            api_key = None

        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables."
            )

        self.client = genai.Client(api_key=api_key)

    def get_response(self, question):
        start_time = time.time()

        try:
            question = (question or "").strip()
            if not question:
                return {
                    "success": False,
                    "error": "Question cannot be empty.",
                    "response": None,
                    "tokens_used": 0,
                    "response_time": 0,
                }

            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=[question],
            )
            response_time = round(time.time() - start_time, 2)

            tokens_used = 0
            usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
            if usage is not None:
                if isinstance(usage, dict):
                    tokens_used = usage.get("total_tokens", 0)
                else:
                    tokens_used = (
                        getattr(usage, "total_token_count", None)
                        or getattr(usage, "total_tokens", None)
                        or 0
                    )

            response_text = getattr(response, "text", None)
            if not response_text:
                candidates = getattr(response, "candidates", None)
                if candidates and isinstance(candidates, list) and len(candidates) > 0:
                    first_candidate = candidates[0]
                    content = getattr(first_candidate, "content", None)
                    if content is not None:
                        parts = getattr(content, "parts", None)
                        if parts and isinstance(parts, list):
                            response_text = "".join(
                                getattr(part, "text", "") for part in parts
                            )

            response_text = (response_text or "").strip()
            if not response_text:
                return {
                    "success": False,
                    "error": "AI returned an empty response.",
                    "response": None,
                    "tokens_used": tokens_used,
                    "response_time": response_time,
                }

            return {
                "success": True,
                "response": response_text,
                "tokens_used": tokens_used,
                "response_time": response_time,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "tokens_used": 0,
                "response_time": 0,
            }