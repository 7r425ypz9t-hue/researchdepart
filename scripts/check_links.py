"""فحص الروابط الداخلية في ملفات Markdown (المسارات النسبية)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = []
for md in ROOT.rglob("*.md"):
    if ".git" in md.parts or "projects" in md.parts:
        continue
    for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        if not (md.parent / link).resolve().exists():
            bad.append(f"{md.relative_to(ROOT)} → {link}")
print("\n".join(bad) or "✓ internal links OK")
sys.exit(1 if bad else 0)
