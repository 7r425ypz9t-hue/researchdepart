"""يتحقق من manifest.yaml وstate.yaml لكل مشروع في projects/."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from rkpos import registry as R  # noqa: E402

errs = []
for p in sorted((ROOT / "projects").glob("RKP-*")):
    for f, s in (("manifest.yaml", "project_manifest"), ("state.yaml", "state")):
        if (p / f).exists():
            errs += [f"{p.name}/{f}: {e}" for e in R.validate(yaml.safe_load((p / f).read_text(encoding="utf-8")), s)]
        else:
            errs.append(f"{p.name}: missing {f}")
print("\n".join(errs) or "✓ projects valid")
sys.exit(1 if errs else 0)
