"""SKL-TERMS — فرض الاتساق المصطلحي وفق knowledge-base/editorial/glossary.yaml."""
from __future__ import annotations
import re

import yaml

from ..paths import ROOT

GLOSSARY = ROOT / "knowledge-base/editorial/glossary.yaml"


def load(path=GLOSSARY) -> list[dict]:
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("terms", []) if path.exists() else []


def check(text: str, terms: list[dict] | None = None) -> list[dict]:
    terms = load() if terms is None else terms
    hits = []
    for t in terms:
        for v in t.get("avoid", []):
            for m in re.finditer(re.escape(v), text):
                hits.append({"found": v, "preferred": t["ar"], "en": t.get("en"), "pos": m.start()})
    return hits
