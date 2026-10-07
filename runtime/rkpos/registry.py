"""تحميل السجلات والتحقق من سلامة الإحالات المتقاطعة (Integrity of the system itself)."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .paths import SPECS, SCHEMAS, WORKFLOWS, ROOT, GOVERNANCE

VIRTUAL_ACTORS = {"HUMAN-AUTHOR", "HUMAN-TECH", "AG-COUNCIL", "ALL"}


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def schema(name: str) -> dict:
    with open(SCHEMAS / f"{name}.schema.json", encoding="utf-8") as f:
        return json.load(f)


def validate(instance, schema_name: str) -> list[str]:
    v = Draft202012Validator(schema(schema_name))
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in v.iter_errors(instance)]


def agents() -> dict[str, dict]:
    out = {}
    for p in sorted(SPECS.glob("AG-*.yaml")):
        d = load_yaml(p)
        out[d["agent_id"]] = d
    return out


def skills() -> dict[str, dict]:
    return {s["id"]: s for s in load_yaml(ROOT / "skills/registry.yaml")["skills"]}


def tools() -> dict[str, dict]:
    return {t["id"]: t for t in load_yaml(ROOT / "tools/registry.yaml")["tools"]}


def memory() -> dict[str, dict]:
    m = load_yaml(ROOT / "memory/layers.yaml")
    return {x["id"]: x for x in m["layers"] + m["stores"]}


def workflows() -> dict[str, dict]:
    return {load_yaml(p)["workflow_id"]: load_yaml(p) for p in sorted(WORKFLOWS.glob("WF-*.yaml"))}


def gates() -> dict[str, dict]:
    return {g["id"]: g for g in load_yaml(GOVERNANCE / "quality_gates.yaml")["gates"]}


def departments() -> dict[str, dict]:
    return {d["id"]: d for d in load_yaml(GOVERNANCE / "departments.yaml")["departments"]}


def check_integrity() -> list[str]:
    """يعيد قائمة الأخطاء؛ القائمة الفارغة تعني أن المنظومة متسقة."""
    errs: list[str] = []
    A, S, T, M, W, G, D = agents(), skills(), tools(), memory(), workflows(), gates(), departments()
    known_actors = set(A) | VIRTUAL_ACTORS

    for aid, a in A.items():
        for e in validate(a, "agent_spec"):
            errs.append(f"{aid}: schema: {e}")
        if a["department"] not in D:
            errs.append(f"{aid}: unknown department {a['department']}")
        for s in a["skills"]:
            if s not in S:
                errs.append(f"{aid}: unknown skill {s}")
        for t in a["tools"]:
            if t not in T:
                errs.append(f"{aid}: unknown tool {t}")
        for m in a["memory"]["read"] + a["memory"]["write"]:
            if m not in M:
                errs.append(f"{aid}: unknown memory {m}")
        refs = (a["handoffs"]["receives_from"] + a["handoffs"]["sends_to"]
                + [c["agent"] for c in a["consult"]] + [e["to"] for e in a["escalation"]] + [a["fallback_agent"]])
        for r in refs:
            if r not in known_actors:
                errs.append(f"{aid}: unknown actor {r}")
        for g in a["quality_gates"]:
            if g not in G:
                errs.append(f"{aid}: unknown gate {g}")
        # Least privilege: لا كتابة مباشرة في الذاكرة المؤسسية أو ذاكرة المؤلف
        for forbidden in ("MEM-INSTITUTIONAL", "MEM-AUTHOR"):
            if forbidden in a["memory"]["write"]:
                errs.append(f"{aid}: write to {forbidden} is forbidden (promotion pipeline only)")
        # استقلال طبقة الإشراف
        if a["type"] == "supervisory" and aid not in ("AG-ORC", "AG-DIR"):
            for w in a["memory"]["write"]:
                if w in ("ST-DRAFT", "ST-EDITED", "ST-APPROVED"):
                    errs.append(f"{aid}: supervisors must not write content stores ({w})")
        # MEM-SOURCE يكتبه AG-SRC وحده
        if "MEM-SOURCE" in a["memory"]["write"] and aid != "AG-SRC":
            errs.append(f"{aid}: only AG-SRC may write MEM-SOURCE")
        # ST-APPROVED لا يكتبه أي وكيل (ينقله المنسق بعد موافقة المؤلف عبر rkpos approve)
        if "ST-APPROVED" in a["memory"]["write"]:
            errs.append(f"{aid}: ST-APPROVED is written only by `rkpos approve` after L4")
        # المراجعون المستقلون
        if aid in ("AG-RED", "AG-PRV", "AG-EVA") and a["model_tier"] != "T4-independent":
            errs.append(f"{aid}: reviewer must use T4-independent tier")

    # تبادلية التسليمات: إذا أرسل X إلى Y فيجب أن يقبل Y من X (أو ALL)
    for aid, a in A.items():
        for to in a["handoffs"]["sends_to"]:
            if to in A and not ({aid, "ALL"} & set(A[to]["handoffs"]["receives_from"])):
                errs.append(f"handoff asymmetry: {aid} -> {to} not accepted by {to}")

    for wid, w in W.items():
        for e in validate(w, "workflow"):
            errs.append(f"{wid}: schema: {e}")
        for st in w["steps"]:
            if "uses" in st and st["uses"] not in W:
                errs.append(f"{wid}/{st['id']}: unknown sub-workflow {st['uses']}")
            if "agent" in st and st["agent"] not in known_actors:
                errs.append(f"{wid}/{st['id']}: unknown agent {st['agent']}")
            if st.get("reviewer") and st["reviewer"] not in known_actors:
                errs.append(f"{wid}/{st['id']}: unknown reviewer {st['reviewer']}")
            if st.get("gate") and st["gate"] not in G:
                errs.append(f"{wid}/{st['id']}: unknown gate {st['gate']}")
            for s in st.get("skills", []):
                if s not in S:
                    errs.append(f"{wid}/{st['id']}: unknown skill {s}")
            if st.get("decision_level") == "L4" and not st.get("human_approval"):
                errs.append(f"{wid}/{st['id']}: L4 step must set human_approval: true")
            if st.get("gate") in ("QG0", "QG6") and st.get("decision_level") != "L4":
                errs.append(f"{wid}/{st['id']}: {st['gate']} requires L4")
    return errs
