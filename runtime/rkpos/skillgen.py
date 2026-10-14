"""يولّد مهارات Claude Code القابلة للاستدعاء (.claude/skills/<slug>/SKILL.md) من سجل المهارات.

لكل مهارة حالتها available_now في skills/registry.yaml ملف SKILL.md: ترويسة (الاسم ووصف عربي لموضع الاستدعاء)،
ثم الغرض والإجراء والمخرجات وطريقة التحقق والوكلاء المستعملون، ثم الدستور المشترك من prompts/constitution.md.
بهذا تصير مهارات «باحث» مهارات فعلية في Claude Code داخل هذا المستودع.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

from . import registry as R
from .paths import ROOT, PROMPTS

HEADER = "<!-- مولَّد بالأمر `rkpos skills-gen` من skills/registry.yaml؛ لا يُحرَّر يدوياً. -->"


def out_dir() -> Path:
    return ROOT / ".claude" / "skills"


def slug(skill_id: str) -> str:
    return "bahith-" + re.sub(r"[^a-z0-9]+", "-", skill_id.removeprefix("SKL-").lower()).strip("-")


def _realization(r: str) -> str:
    kind, _, arg = str(r).partition(":")
    if kind == "prompt":
        return "إجراء مكتوب يُحقن في سياق الوكيل"
    if kind == "code":
        return f"شيفرة في المستودع: `{arg}`" if arg else "شيفرة في المستودع"
    if kind == "claude_skill":
        return f"مهارة Claude قائمة لدى المؤلف: `{arg}`"
    if kind == "api":
        return "واجهة خارجية"
    if kind == "config":
        return f"إعدادات: `{arg}`"
    return str(r)


def constitution() -> str:
    """الدستور المشترك بعناوين مخفّضة درجةً لتندرج تحت قسمه في ملف المهارة."""
    f = PROMPTS / "constitution.md"
    if not f.exists():
        return ""
    lines = f.read_text(encoding="utf-8").splitlines()
    body = [l for l in lines if not l.startswith("# ")]
    return "\n".join(("#" + l) if l.startswith("## ") else l for l in body).strip()


def render(sk: dict, agents: dict, tools: dict, const: str) -> str:
    users = [a for aid, a in agents.items() if sk["id"] in a.get("skills", [])]
    desc = (f"استدعِ هذه المهارة عند الحاجة إلى «{sk['name_ar']}» في عمل من أعمال مؤسسة «باحث» أو ما في معناه. "
            f"{sk['purpose']} تعمل بانضباط صفر تلفيق، وكل قرار نهائي للمؤلف.")
    lines = ["---", f"name: {slug(sk['id'])}", f"description: {json.dumps(desc, ensure_ascii=False)}", "---", "", HEADER, "",
             f"# {sk['name_ar']} — {sk['id']}", "", "## الغرض", "", sk["purpose"], "",
             "## متى تُستدعى", "",
             f"- حين يُطلب «{sk['name_ar']}» صراحةً، أو تقتضيه خطوة في سير عمل مشروع من مشاريع «باحث» (projects/RKP-…).",
             "- حين يكلّف المؤلف أحد الوكلاء المذكورين أدناه بمهمة تدخل في هذا الاختصاص.", "",
             "## الإجراء", "", *[f"{i}. {s}" for i, s in enumerate(sk["procedure"], 1)], "",
             "## المخرجات", "", *[f"- `{o}`" for o in sk["outputs"]], "",
             "## طريقة التحقق", "", *[f"- {_realization(r)}" for r in sk["realization"]]]
    if sk.get("tools"):
        lines += ["", "## الأدوات", "", *[f"- `{t}` — {tools.get(t, {}).get('function', '')}".rstrip(" —") for t in sk["tools"]]]
    if users:
        lines += ["", "## الوكلاء المستعملون", "", *[f"- `{a['agent_id']}` — {a['name_ar']}" for a in users]]
    lines += ["", "## قواعد التشغيل في هذا المستودع", "",
              "- اقرأ بيان المشروع (`manifest.yaml`) وحالته (`state.yaml`) قبل العمل، واكتب في مسارات المشروع المسموحة وحدها.",
              "- سجّل المصادر في `research/sources.jsonl` والادعاءات في `evidence/claims.jsonl`، وافحص المسودة بالأمر "
              "`rkpos check-manuscript` قبل التسليم.",
              "- لا تعلن تنفيذ ما لم يُنفَّذ، ولا تحققاً لم يجرِ."]
    if const:
        lines += ["", "## الدستور المشترك", "", const]
    return "\n".join(lines) + "\n"


def build() -> dict[Path, str]:
    A, T = R.agents(), R.tools()
    const = constitution()
    return {out_dir() / slug(s["id"]) / "SKILL.md": render(s, A, T, const)
            for s in R.skills().values() if s.get("status") == "available_now"}


def generate(check: bool = False) -> list[Path]:
    """يكتب ملفات المهارات؛ في وضع check يعيد غير المطابق منها دون كتابة."""
    stale = []
    for p, content in build().items():
        if not p.exists() or p.read_text(encoding="utf-8") != content:
            stale.append(p)
            if not check:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
    return stale
