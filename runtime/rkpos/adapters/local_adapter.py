"""Local models via an OpenAI-compatible endpoint (Ollama / vLLM / LM Studio). LOCAL_LLM_BASE_URL مطلوب.
مناسب لمواد AUTHOR_ONLY التي لا تغادر الجهاز."""
from __future__ import annotations
import os

from .openai_adapter import OpenAIAdapter


class LocalAdapter(OpenAIAdapter):
    provider = "local"
    base_url_env = "LOCAL_LLM_BASE_URL"
    key_env = "LOCAL_LLM_API_KEY"

    def available(self) -> bool:
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get(self.base_url_env)) and not self.model.isupper()
