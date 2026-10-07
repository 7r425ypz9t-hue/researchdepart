"""سجل المصادر (MEM-SOURCE) — إضافة سجل مع فرض قاعدة «لا DOI غير متحقق»."""
from __future__ import annotations
import json
from pathlib import Path

from .. import registry as R
from ..paths import ROOT

DEFAULT = ROOT / "knowledge-base/sources/sources.jsonl"
TIER_BY_TYPE = {t: tier["tier"] for tier in R.load_yaml(ROOT / "governance/source_hierarchy.yaml")["tiers"] for t in tier["types"]}


def load(path: Path = DEFAULT) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def next_id(records: list[dict]) -> str:
    n = max([int(r["Source_ID"][4:]) for r in records] or [0]) + 1
    return f"SRC-{n:06d}"


def add(record: dict, path: Path = DEFAULT) -> dict:
    recs = load(path)
    record = dict(record)
    record.setdefault("Source_ID", next_id(recs))
    record.setdefault("Tier", TIER_BY_TYPE.get(record.get("Source_Type")))
    if record.get("DOI") and any((r.get("DOI") or "").lower() == record["DOI"].lower() for r in recs):
        raise ValueError(f"duplicate DOI {record['DOI']}")
    errs = R.validate(record, "source")
    if errs:
        raise ValueError(errs)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
