"""ترقية المعرفة — لا يدخل عنصر الذاكرة المؤسسية/ذاكرة المؤلف إلا بعد اعتماد المؤلف."""
from __future__ import annotations
import json

from . import audit, registry as R
from .paths import ROOT

CANDIDATES = ROOT / "knowledge-base/candidates/candidates.jsonl"
# مواد AUTHOR_ONLY لا تمر بأي ملف متتبع في git — مسارها الخاص مستثنى في .gitignore
PRIVATE_DIR = ROOT / "memory/author/private"
PRIVATE_CANDIDATES = PRIVATE_DIR / "candidates.jsonl"
LAYER_FILES = {
    "MEM-INSTITUTIONAL": ROOT / "knowledge-base/institutional/items.jsonl",
    "MEM-AUTHOR": PRIVATE_DIR / "items.jsonl",
    "MEM-RESEARCH": ROOT / "knowledge-base/research/items.jsonl",
    "MEM-EDITORIAL": ROOT / "knowledge-base/editorial/items.jsonl",
}


def _read(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def _append(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _candidates_file(item: dict):
    return PRIVATE_CANDIDATES if item.get("Access_Level") == "AUTHOR_ONLY" else CANDIDATES


def propose(item: dict) -> dict:
    item = {**item, "Layer": "ST-KB-CANDIDATES", "Verified": False, "Approved_By": None}
    errs = R.validate(item, "memory_item")
    if errs:
        raise ValueError(errs)
    target = _candidates_file(item)
    _append(target, item)
    audit.log(item["Created_By"], "kb_propose", project=item.get("Project"), files_changed=[str(target.relative_to(ROOT))])
    return item


def promote(memory_id: str, target_layer: str, approved_by: str) -> dict:
    cands = {c["Memory_ID"]: c for c in _read(CANDIDATES) + _read(PRIVATE_CANDIDATES)}
    if memory_id not in cands:
        raise KeyError(memory_id)
    if target_layer in ("MEM-INSTITUTIONAL", "MEM-AUTHOR") and approved_by != "HUMAN-AUTHOR":
        raise PermissionError("promotion to institutional/author memory requires HUMAN-AUTHOR (L4)")
    if cands[memory_id].get("Access_Level") == "AUTHOR_ONLY" and target_layer != "MEM-AUTHOR":
        raise PermissionError("AUTHOR_ONLY items may only be promoted to MEM-AUTHOR")
    item = {**cands[memory_id], "Layer": target_layer, "Verified": True, "Approved_By": approved_by,
            "Version": cands[memory_id]["Version"] + 1}
    errs = R.validate(item, "memory_item")
    if errs:
        raise ValueError(errs)
    _append(LAYER_FILES[target_layer], item)
    audit.log("AG-KNW", "kb_promote", project=item.get("Project"), files_changed=[str(LAYER_FILES[target_layer].relative_to(ROOT))],
              decision=f"{memory_id} -> {target_layer}", decision_level="L4" if target_layer in ("MEM-INSTITUTIONAL", "MEM-AUTHOR") else "L2",
              approval=approved_by)
    return item


def current(layer: str) -> dict[str, dict]:
    """أحدث إصدار لكل عنصر في الطبقة (السجل إلحاقي؛ الإصدارات السابقة محفوظة)."""
    out: dict[str, dict] = {}
    for it in _read(LAYER_FILES[layer]):
        if it["Memory_ID"] not in out or it["Version"] >= out[it["Memory_ID"]]["Version"]:
            out[it["Memory_ID"]] = it
    return out


def amend(memory_id: str, layer: str, new_content: str, approved_by: str, reason: str) -> dict:
    """إصدار جديد لعنصر معتمد (لا محو): Version+1، والسبب يُسجَّل في الوسوم والتدقيق."""
    if layer in ("MEM-INSTITUTIONAL", "MEM-AUTHOR") and approved_by != "HUMAN-AUTHOR":
        raise PermissionError("amending institutional/author memory requires HUMAN-AUTHOR (L4)")
    cur = current(layer)
    if memory_id not in cur:
        raise KeyError(memory_id)
    item = {**cur[memory_id], "Content": new_content, "Version": cur[memory_id]["Version"] + 1,
            "Approved_By": approved_by, "Tags": list(cur[memory_id].get("Tags", [])) + [f"amended:{reason}"]}
    errs = R.validate(item, "memory_item")
    if errs:
        raise ValueError(errs)
    _append(LAYER_FILES[layer], item)
    audit.log("AG-KNW", "kb_amend", project=item.get("Project"), files_changed=[str(LAYER_FILES[layer].relative_to(ROOT))],
              decision=f"{memory_id} v{item['Version']} ({reason})", decision_level="L4" if layer in ("MEM-INSTITUTIONAL", "MEM-AUTHOR") else "L2",
              approval=approved_by)
    return item
