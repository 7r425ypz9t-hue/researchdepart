"""المثبّت بسطر واحد (منقول من «تراث»): التحديث لا يمسّ بيانات المؤلف، والتثبيت الجديد، ورفض مجلد غريب.
يُختبر مثبّت ماك ولينكس دائماً، ومثبّت ويندوز حيث توجد pwsh."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
USER_FILES = {
    "projects/RKP-2026-0001/plan.yaml": "title: مشروعي\n",
    "memory/author/private/items.jsonl": '{"id": "M1"}\n',
    "logs/audit.jsonl": '{"event": "my-own-trail"}\n',
    "logs/kpi_baseline.json": "{}\n",
    ".env": "ANTHROPIC_API_KEY=x\n",
    "knowledge-base/institutional/items.jsonl": '{"k": 1}\n',
    "workspace/vault/registry.jsonl": '{"id": "AST-1"}\n',
}


def _copy_repo(dest: Path):
    shutil.copytree(REPO, dest, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.egg-info"))


def _run_unix(env, home):
    return subprocess.run(["bash", str(REPO / "launchers/install_unix.sh")], env=env, capture_output=True, text=True, cwd=home)


def _run_ps(env, home, root):
    pwsh = shutil.which("pwsh")
    return subprocess.run([pwsh, "-NoProfile", "-File", str(REPO / "launchers/install_windows.ps1"), "-Source", str(REPO),
                           "-Root", str(root), "-NoLaunch"], env=env, capture_output=True, text=True, cwd=home)


RUNNERS = ["unix", pytest.param("windows", marks=pytest.mark.skipif(not shutil.which("pwsh"), reason="لا pwsh"))]


def _env(home: Path, root: Path):
    return {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "BAHITH_SOURCE": str(REPO),
            "BAHITH_ROOT": str(root), "BAHITH_NO_LAUNCH": "1"}


def _install(kind, home, root):
    r = _run_unix(_env(home, root), home) if kind == "unix" else _run_ps(_env(home, root), home, root)
    return r


@pytest.mark.parametrize("kind", RUNNERS)
def test_update_keeps_author_data(tmp_path, kind):
    home, root = tmp_path / "home", tmp_path / "home/Documents/Bahith"
    home.mkdir()
    _copy_repo(root)
    for rel, text in USER_FILES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    (root / "runtime/rkpos/obsolete_module.py").write_text("# حُذف من الإصدار الجديد\n")
    r = _install(kind, home, root)
    assert r.returncode == 0, r.stdout + r.stderr
    for rel, text in USER_FILES.items():
        assert (root / rel).read_text(encoding="utf-8") == text, rel
    assert not (root / "runtime/rkpos/obsolete_module.py").exists()          # الشيفرة من الإصدار الجديد وحده
    assert (root / "runtime/rkpos/__main__.py").exists()
    assert (Path(str(root) + ".previous") / "projects/RKP-2026-0001/plan.yaml").exists()   # النسخة السابقة احتياطاً
    rec = json.loads((home / ".rkpos/install.json").read_text(encoding="utf-8-sig"))
    assert Path(rec["root"]).resolve() == root.resolve()


@pytest.mark.parametrize("kind", RUNNERS)
def test_fresh_install_and_refuse_foreign_folder(tmp_path, kind):
    home = tmp_path / "home"
    home.mkdir()
    fresh = home / "Documents/Bahith"
    r = _install(kind, home, fresh)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (fresh / "launchers/user-data.txt").exists() and not (fresh / ".git").exists()
    foreign = home / "Documents/Other"
    foreign.mkdir(parents=True)
    (foreign / "keep.txt").write_text("لا يُمسّ")
    r = _install(kind, home, foreign)
    assert r.returncode != 0 and (foreign / "keep.txt").read_text() == "لا يُمسّ"


def test_user_data_list_covers_ignored_author_paths():
    lines = [ln.strip() for ln in (REPO / "launchers/user-data.txt").read_text(encoding="utf-8").splitlines()]
    entries = {ln for ln in lines if ln and not ln.startswith("#")}
    for must in (".env", "projects/RKP-*", "workspace", "logs/*", "memory/author", "knowledge-base/*/*.jsonl",
                 "publishing/dashboard", "validation/reports", "midad-private-backup.tar.gz"):
        assert must in entries, must
