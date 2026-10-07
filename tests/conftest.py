import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
COPY = ["agents", "schemas", "workflows", "governance", "config", "prompts", "skills", "tools", "memory", "validation"]


@pytest.fixture
def sandbox(tmp_path):
    """نسخة معزولة من المستودع لتشغيل الأوامر التي تكتب ملفات."""
    for d in COPY:
        shutil.copytree(REPO / d, tmp_path / d)
    for d in ("projects", "logs", "knowledge-base"):
        (tmp_path / d).mkdir()
    env = {**os.environ, "RKPOS_ROOT": str(tmp_path), "PYTHONPATH": str(REPO / "runtime")}

    def run(*args, ok=True):
        r = subprocess.run([sys.executable, "-m", "rkpos", *args], cwd=tmp_path, env=env, capture_output=True, text=True)
        if ok and r.returncode != 0:
            raise AssertionError(f"rkpos {args} failed:\n{r.stdout}\n{r.stderr}")
        return r
    run.root = tmp_path
    return run
