"""فحص أمني خفيف: أسرار في الملفات المتتبعة + سلامة مصفوفة الصلاحيات (AG-SEC في MVP)."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "anthropic_key": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "openai_key": r"sk-(proj-)?[A-Za-z0-9]{32,}",
    "google_key": r"AIza[0-9A-Za-z_\-]{35}",
    "github_token": r"gh[pousr]_[A-Za-z0-9]{36,}",
    "private_key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "zotero_key_assignment": r"ZOTERO_API_KEY\s*=\s*[A-Za-z0-9]{20,}",
}
files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
hits = []
for f in files:
    p = ROOT / f
    if not p.is_file() or p.stat().st_size > 2_000_000:
        continue
    try:
        txt = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if "AUTHOR_ONLY:BEGIN" in txt and f not in ("runtime/rkpos/runner.py", "scripts/security_scan.py") and not f.startswith("tests/"):
        hits.append(f"{f}: contains AUTHOR_ONLY style contract")
    for name, pat in PATTERNS.items():
        if re.search(pat, txt):
            hits.append(f"{f}: possible {name}")
hits += [f"{f}: AUTHOR_ONLY path is tracked by git" for f in files if f.startswith("memory/author/private/")]
if (ROOT / ".env").exists() and ".env" in files:
    hits.append(".env is tracked by git")
sys.path.insert(0, str(ROOT / "runtime"))
from rkpos import registry  # noqa: E402
for aid, a in registry.agents().items():
    if a["type"] in ("utility",) and "MEM-AUTHOR" in a["memory"]["read"]:
        hits.append(f"{aid}: utility agent must not read MEM-AUTHOR")
print("\n".join(hits) or "✓ no secrets or permission violations found")
sys.exit(1 if hits else 0)
