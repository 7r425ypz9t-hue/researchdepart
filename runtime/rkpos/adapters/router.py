"""Routing Policy: فئة الوكيل ← مزود:نموذج، مع البدائل وقاعدة الاستقلال (المراجع ≠ الكاتب)."""
from __future__ import annotations

from .. import registry as R, cost as C
from ..paths import CONFIG
from .base import AdapterUnavailable, Completion, ManualAdapter, ModelAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .local_adapter import LocalAdapter

ADAPTERS = {"anthropic": AnthropicAdapter, "openai": OpenAIAdapter, "google": GoogleAdapter, "local": LocalAdapter}


def policy() -> dict:
    return R.load_yaml(CONFIG / "model_routing.yaml")


def candidates(tier: str) -> list[str]:
    t = policy()["tiers"][tier]
    return [t["primary"], *t.get("fallback", [])]


def make(spec: str) -> ModelAdapter:
    provider, model = spec.split(":", 1)
    return ADAPTERS[provider](model)


def resolve(agent_id: str, author_model: str | None = None, manual_ok: bool = True) -> tuple[ModelAdapter, list[str]]:
    """يختار أول محوّل متاح لفئة الوكيل. للمراجعين (T4) يتخطى أي نموذج يطابق نموذج الكتابة."""
    a = R.agents()[agent_id]
    warnings = []
    specs = candidates(a["model_tier"])
    if a["model_tier"] == "T4-independent" and author_model:
        indep = [s for s in specs if s != author_model and s.split(":")[0] != author_model.split(":")[0]]
        if not any(make(s).available() for s in indep):
            warnings.append("INDEPENDENCE_DEGRADED: لا مزود مستقل متاح؛ المراجعة بنموذج من مزود الكاتب")
        else:
            specs = indep
    for s in specs:
        ad = make(s)
        if ad.available():
            return ad, warnings
    if manual_ok:
        warnings.append("NO_PROVIDER_CONFIGURED: الوضع اليدوي (حزمة برومبت للنسخ)")
        return ManualAdapter(specs[0]), warnings
    raise AdapterUnavailable(f"no adapter available for {agent_id}")


def run(agent_id: str, system: str, user: str, project: str | None, stage: str | None = None,
        author_model: str | None = None, **kw) -> tuple[Completion, list[str]]:
    ad, warnings = resolve(agent_id, author_model)
    comp = ad.complete(system, user, **kw)
    if ad.provider != "manual":
        C.record(comp.model, comp.input_tokens, comp.output_tokens, project, agent_id, stage)
    return comp, warnings
