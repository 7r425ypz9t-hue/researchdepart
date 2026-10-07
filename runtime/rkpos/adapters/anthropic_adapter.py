"""Anthropic adapter — يستعمل حزمة anthropic الرسمية (pip install anthropic)."""
from __future__ import annotations
import os

from .base import Completion, ModelAdapter, AdapterUnavailable


class AnthropicAdapter(ModelAdapter):
    provider = "anthropic"

    def available(self) -> bool:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_PROFILE"))

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        try:
            import anthropic
        except ImportError as e:
            raise AdapterUnavailable("pip install anthropic") from e
        client = anthropic.Anthropic()
        kwargs = {}
        if effort:
            kwargs["output_config"] = {"effort": effort}
        # البث يجنّب مهلات HTTP للمخرجات الطويلة (فصول كاملة)
        with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": user}],
            **kwargs,
        ) as stream:
            msg = stream.get_final_message()
        refused = msg.stop_reason == "refusal"
        text = "" if refused else "".join(b.text for b in msg.content if b.type == "text")
        return Completion(text=text, model=f"anthropic:{self.model}", input_tokens=msg.usage.input_tokens,
                          output_tokens=msg.usage.output_tokens, stop_reason=msg.stop_reason, refused=refused)
