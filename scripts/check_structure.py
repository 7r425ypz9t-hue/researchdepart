"""يفحص وجود البنية الإلزامية للمستودع (القسم 25) وملفات كل وكيل الثمانية (القسم 26)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = ["governance", "agents/core", "agents/specialists", "agents/supervisors", "agents/utilities", "agents/on-demand",
                 "prompts", "skills", "workflows", "schemas", "tools", "connectors", "memory", "knowledge-base", "projects",
                 "templates", "validation", "publishing", "logs", "tests", "documentation"]
AGENT_FILES = ["agent.yaml", "system_prompt.md", "tools.yaml", "permissions.yaml", "memory.yaml", "handoffs.yaml", "tests.yaml", "README.md"]

errs = [f"missing dir: {d}" for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
for t in ("core", "specialists", "supervisors", "utilities", "on-demand"):
    for ad in (ROOT / "agents" / t).iterdir() if (ROOT / "agents" / t).is_dir() else []:
        errs += [f"{ad.relative_to(ROOT)}: missing {f}" for f in AGENT_FILES if not (ad / f).exists()]
print("\n".join(errs) or "✓ structure OK")
sys.exit(1 if errs else 0)
