"""Google adapter (pip install google-genai). GOOGLE_API_KEY مطلوب."""
from __future__ import annotations
import os

from .base import Completion, ModelAdapter, AdapterUnavailable


class GoogleAdapter(ModelAdapter):
    provider = "google"

    def available(self) -> bool:
        try:
            from google import genai  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get("GOOGLE_API_KEY")) and not self.model.isupper()

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise AdapterUnavailable("pip install google-genai") from e
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        r = client.models.generate_content(model=self.model, contents=user,
                                           config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens))
        um = getattr(r, "usage_metadata", None)
        return Completion(text=r.text or "", model=f"google:{self.model}",
                          input_tokens=getattr(um, "prompt_token_count", 0) or 0,
                          output_tokens=getattr(um, "candidates_token_count", 0) or 0)
