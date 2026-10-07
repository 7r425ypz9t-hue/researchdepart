"""OpenAI adapter (pip install openai). يُستخدم افتراضياً لطبقة T4-independent لضمان استقلال المراجعة."""
from __future__ import annotations
import os

from .base import Completion, ModelAdapter, AdapterUnavailable


class OpenAIAdapter(ModelAdapter):
    provider = "openai"
    base_url_env = None
    key_env = "OPENAI_API_KEY"

    def available(self) -> bool:
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get(self.key_env)) and not self.model.isupper()  # placeholder IDs غير مهيأة

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise AdapterUnavailable("pip install openai") from e
        kw = {"base_url": os.environ[self.base_url_env]} if self.base_url_env else {}
        client = OpenAI(api_key=os.environ.get(self.key_env, "local"), **kw)
        r = client.chat.completions.create(model=self.model, max_tokens=max_tokens,
                                           messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        ch = r.choices[0]
        return Completion(text=ch.message.content or "", model=f"{self.provider}:{self.model}",
                          input_tokens=getattr(r.usage, "prompt_tokens", 0), output_tokens=getattr(r.usage, "completion_tokens", 0),
                          stop_reason=ch.finish_reason)
