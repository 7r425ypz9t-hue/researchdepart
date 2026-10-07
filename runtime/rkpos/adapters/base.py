from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Completion:
    text: str
    model: str                       # provider:model
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None
    refused: bool = False
    raw: dict = field(default_factory=dict)


class AdapterUnavailable(RuntimeError):
    """المزود غير مهيأ (لا مفتاح/لا حزمة) — يُجرّب البديل التالي."""


class ModelAdapter:
    provider = "base"

    def __init__(self, model: str):
        self.model = model

    def available(self) -> bool:
        raise NotImplementedError

    def complete(self, system: str, user: str, max_tokens: int = 16000, effort: str | None = None) -> Completion:
        raise NotImplementedError


class ManualAdapter(ModelAdapter):
    """الوضع اليدوي: لا استدعاء API. يُنتج حزمة برومبت جاهزة للصق في Claude/ChatGPT
    ثم يُعاد المخرج عبر `rkpos record-output`. متاح دائماً — هذا هو تشغيل MVP بلا مفاتيح."""
    provider = "manual"

    def available(self) -> bool:
        return True

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        return Completion(text="", model=f"manual:{self.model}", stop_reason="manual_pending")
