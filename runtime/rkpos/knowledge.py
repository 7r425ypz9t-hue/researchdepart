"""ترقية المعرفة — لا يدخل عنصر الذاكرة المؤسسية/ذاكرة المؤلف إلا بعد اعتماد المؤلف."""
from __future__ import annotations
import json

from . import audit, registry as R
from .paths import ROOT

CANDIDATES = ROOT / "knowledge-base/candidates/candidates.jsonl"
LAYER_FILES = {
    "MEM-INSTITUTIONAL": ROOT / "knowledge-base/institutional/items.jsonl",
    "MEM-AUTHOR": ROOT / "memory/author/items.jsonl",
    "MEM-RESEARCH": ROOT / "knowledge-base/research/items.jsonl",
    "MEM-EDITORIAL": ROOT / "knowledge-base/editorial/items.jsonl",
}


def _read(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def _append(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def propose(item: dict) -> dict:
    item = {**item, "Layer": "ST-KB-CANDIDATES", "Verified": False, "Approved_By": None}
    errs = R.validate(item, "memory_item")
    if errs:
        raise ValueError(errs)
    _append(CANDIDATES, item)
    audit.log(item["Created_By"], "kb_propose", project=item.get("Project"), files_changed=[str(CANDIDATES.relative_to(ROOT))])
    return item


def promote(memory_id: str, target_layer: str, approved_by: str) -> dict:
    cands = {c["Memory_ID"]: c for c in _read(CANDIDATES)}
    if memory_id not in cands:
        raise KeyError(memory_id)
    if target_layer in ("MEM-INSTITUTIONAL", "MEM-AUTHOR") and approved_by != "HUMAN-AUTHOR":
        raise PermissionError("promotion to institutional/author memory requires HUMAN-AUTHOR (L4)")
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
