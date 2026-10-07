"""Routing Policy: فئة الوكيل ← مزود:نموذج، مع البدائل وقاعدة الاستقلال (المراجع ≠ الكاتب)."""
from __future__ import annotations

from .. import registry as R, cost as C
from ..paths import CONFIG
from .base import AdapterUnavailable, Completion, ManualAdapter, ModelAdapter
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .local_adapter import LocalAdapter
from .claude_code_adapter import ClaudeCodeAdapter
import os

ADAPTERS = {"anthropic": AnthropicAdapter, "openai": OpenAIAdapter, "google": GoogleAdapter, "local": LocalAdapter,
            "claude_code": ClaudeCodeAdapter}
# المحرّكات: auto (مفاتيح API ثم Claude Code ثم اليدوي) · claude_code (أداة Claude Code أولاً) · api (مفاتيح فقط) · manual
ENGINES = ("auto", "claude_code", "api", "manual")
FAMILY = {"claude_code": "anthropic"}  # Claude Code يشغّل نماذج Anthropic: لا يُعدّ مستقلاً عنها في المراجعة


def policy() -> dict:
    return R.load_yaml(CONFIG / "model_routing.yaml")


def candidates(tier: str) -> list[str]:
    t = policy()["tiers"][tier]
    return [t["primary"], *t.get("fallback", [])]


def make(spec: str) -> ModelAdapter:
    provider, model = spec.split(":", 1)
    return ADAPTERS[provider](model)


def _family(spec: str) -> str:
    p = spec.split(":")[0]
    return FAMILY.get(p, p)


def _engine_specs(specs: list[str], engine: str) -> list[str]:
    cc = [f"claude_code:{s.split(':', 1)[1]}" for s in specs if s.startswith("anthropic:")]
    if engine == "claude_code":
        return cc + specs
    if engine == "api":
        return specs
    return specs + cc  # auto


def resolve(agent_id: str, author_model: str | None = None, manual_ok: bool = True,
            engine: str | None = None) -> tuple[ModelAdapter, list[str]]:
    """يختار أول محوّل متاح لفئة الوكيل. للمراجعين (T4) يتخطى أي نموذج يطابق نموذج الكتابة."""
    a = R.agents()[agent_id]
    warnings = []
    engine = engine or os.environ.get("RKPOS_ENGINE", "auto")
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine}; choose one of {ENGINES}")
    base = candidates(a["model_tier"])
    if engine == "manual":
        return ManualAdapter(base[0]), ["MANUAL_ENGINE: حزمة برومبت للنسخ"]
    specs = _engine_specs(base, engine)
    if a["model_tier"] == "T4-independent" and author_model:
        indep = [s for s in specs if s != author_model and _family(s) != _family(author_model)]
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
        return ManualAdapter(base[0]), warnings
    raise AdapterUnavailable(f"no adapter available for {agent_id}")


def run(agent_id: str, system: str, user: str, project: str | None, stage: str | None = None,
        author_model: str | None = None, engine: str | None = None, **kw) -> tuple[Completion, list[str]]:
    ad, warnings = resolve(agent_id, author_model, engine=engine)
    comp = ad.complete(system, user, **kw)
    if ad.provider != "manual":
        C.record(comp.model, comp.input_tokens, comp.output_tokens, project, agent_id, stage,
                 usd=comp.raw.get("total_cost_usd"))
    return comp, warnings
