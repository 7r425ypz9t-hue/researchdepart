"""مؤسسة «باحث»: الإدارات، وهوياتها، والأنواع الجديدة، والتسويق والتصميم، والاسم الجديد."""
import json
import sys
from pathlib import Path

import pytest
import yaml

from test_book import FAKE, bk, _new  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "runtime"))


def test_institution_structure_is_consistent():
    from rkpos import institution as INS, registry as R
    assert INS.check() == []
    divs = INS.divisions()
    assert {d for d, v in divs.items() if v["kind"] == "specialized"} == {
        "DIV-CREATIVE", "DIV-ARTICLE", "DIV-ACADEMIC", "DIV-ECOCULT", "DIV-THOUGHT"}
    assert {d for d, v in divs.items() if v["kind"] == "support"} == {"DIV-TECH", "DIV-DESIGN", "DIV-MARKETING"}
    assert divs["DIV-DESIGN"]["central"] and set(divs["DIV-DESIGN"]["sub_units"]) == {
        d for d, v in divs.items() if v["kind"] == "specialized"}
    colors = [v["theme"]["primary"] for v in divs.values()]
    assert len(set(colors)) == len(colors)                         # لكل إدارة لونها المميز
    assert INS.division_for_type("play") == "DIV-CREATIVE"
    assert INS.division_for_type("op_ed") == "DIV-ARTICLE"
    assert INS.division_for_type("journal_article") == "DIV-ACADEMIC"
    assert INS.division_for_type("economic_study") == "DIV-ECOCULT"
    assert INS.division_for_type("development_study") == "DIV-THOUGHT"
    assert {"AG-ECO", "AG-DSN", "AG-MKT"} <= set(R.agents())
    assert INS.config()["name_ar"] == "باحث"


def test_new_types_create_projects_in_their_division(bk):
    pid, out = _new(bk, "مسرحية", "--type", "play")
    assert out["genre"] == "creative" and out["workflow"] == "WF-NOVEL"
    m = yaml.safe_load((bk.root / "projects" / pid / "manifest.yaml").read_text(encoding="utf-8"))
    assert m["division"] == "DIV-CREATIVE"
    pid2, out2 = _new(bk, "اقتصاد المهرجانات", "--type", "economic_study", "--pages", "10")
    assert out2["workflow"] == "WF-APPLIED-STUDY" and "AG-ECO" in out2["agents"]["specialist"]


def test_marketing_requires_approved_work_then_builds_pack(bk):
    pid, _ = _new(bk, "عمود", "--type", "op_ed")
    sys_env = dict(RKPOS_ROOT=str(bk.root))
    import os, subprocess
    env = {**os.environ, **sys_env, "PYTHONPATH": str(REPO / "runtime")}
    code = ("import sys; from rkpos import marketing as M\n"
            "try:\n M.pack(sys.argv[1], 'claude_code'); print('NO')\n"
            "except PermissionError: print('BLOCKED')\n")
    r = subprocess.run([sys.executable, "-c", code, pid], cwd=bk.root, env={**env, "RKPOS_CLAUDE_BIN": os.environ.get("RKPOS_CLAUDE_BIN", "")},
                       capture_output=True, text=True)
    assert "BLOCKED" in r.stdout, r.stderr
    # اعتماد العمود عبر الطيار المباشر ثم الحزمة
    yaml.safe_load(bk("autopilot", pid, "--engine", "claude_code", "--mode", "direct").stdout)
    bk("autopilot", pid, "--engine", "claude_code", "--answer", "approve")
    fake = Path(bk.root) / "fake_claude"
    r = subprocess.run([sys.executable, "-c", "import sys,json; from rkpos import marketing as M; print(json.dumps(M.pack(sys.argv[1],'claude_code')))", pid],
                       cwd=bk.root, env={**env, "RKPOS_CLAUDE_BIN": str(fake)}, capture_output=True, text=True)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert (bk.root / out["pack"]).exists() and (bk.root / out["design"]).exists()


def test_word_export_uses_division_colors():
    import io
    from docx import Document
    from rkpos.export import to_docx
    from rkpos import institution as INS
    th = INS.theme("DIV-ECOCULT")
    doc = Document(io.BytesIO(to_docx("## عنوان\n\nنص.", "دراسة", theme=th)))
    title_run = doc.paragraphs[0].runs[0]
    assert str(title_run.font.color.rgb) == th["primary"].lstrip("#").upper()
