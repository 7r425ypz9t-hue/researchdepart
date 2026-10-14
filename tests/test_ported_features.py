"""الميزات المنقولة من «تراث»: خزنة الأصول وسلامتها، ومهارات Claude Code، وتثليث الأدلة، وخط أساس المؤشرات."""
import json
import os
import stat
import zipfile

import yaml

from rkpos import skillgen
from rkpos.verify import claims


# ------------------------------------------------------------------ خزنة الأصول
def test_vault_add_dedup_readonly_verify_backup(sandbox):
    root = sandbox.root
    doc = root / "وثيقة.pdf"
    doc.write_bytes(b"%PDF-1.4 asset body")
    pid = yaml.safe_load(sandbox("new-project", "دراسة", "--type", "cultural_study").stdout)["project_id"]
    r = yaml.safe_load(sandbox("vault", "add", str(doc), "--project", pid, "--provenance", "أرشيف المؤسسة",
                               "--rights", "استعمال بحثي").stdout)
    assert r["id"].startswith("AST-") and r["id"].endswith("-0001") and r["kind"] == "document" and not r["duplicate"]
    stored = root / "workspace/vault" / r["vault_path"]
    assert stored.exists() and r["vault_path"].startswith(f"originals/{r['sha256'][:2]}/{r['sha256']}")
    assert not stored.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)   # للقراءة فقط

    # الملف نفسه باسم آخر لا يُنشئ نسخة ولا سجلاً ثانياً
    copy = root / "نسخة.pdf"
    copy.write_bytes(doc.read_bytes())
    again = yaml.safe_load(sandbox("vault", "add", str(copy)).stdout)
    assert again["duplicate"] and again["id"] == r["id"]
    reg = [json.loads(l) for l in (root / "workspace/vault/registry.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(reg) == 1 and reg[0]["provenance"] == "أرشيف المؤسسة" and reg[0]["project"] == pid
    assert {"sha256", "filename", "size", "mime", "kind", "rights", "depositor", "created_at", "integrity", "last_verified"} <= set(reg[0])

    # مشروع غير موجود يُرفض
    assert sandbox("vault", "add", str(doc), "--project", "RKP-1999-0001", ok=False).returncode != 0

    # الفحص: سليم، ثم معدَّل، ثم مفقود
    other = root / "صورة.png"
    other.write_bytes(b"\x89PNG image")
    img = yaml.safe_load(sandbox("vault", "add", str(other)).stdout)
    assert img["id"].endswith("-0002") and img["kind"] == "image"
    ok = yaml.safe_load(sandbox("vault", "verify").stdout)
    assert ok["ok"] == 2 and not ok["missing"] and not ok["altered"]
    os.chmod(stored, 0o644)
    stored.write_bytes(b"tampered")
    (root / "workspace/vault" / img["vault_path"]).unlink()
    bad = sandbox("vault", "verify", ok=False)
    rep = yaml.safe_load(bad.stdout)
    assert bad.returncode == 2 and rep["altered"] == [r["id"]] and rep["missing"] == [img["id"]]
    listed = yaml.safe_load(sandbox("vault", "list").stdout)
    assert {x["id"]: x["integrity"] for x in listed} == {r["id"]: "altered", img["id"]: "missing"}

    # النسخة الاحتياطية على نمط BagIt
    out = sandbox("backup").stdout.strip().split("→ ")[-1]
    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        assert {"data/registry.jsonl", "manifest-sha256.txt", "bag-info.txt", "bagit.txt"} <= names
        assert f"data/vault/{r['vault_path']}" in names
        man = z.read("manifest-sha256.txt").decode()
        assert "data/registry.jsonl" in man and "Payload-Oxum" in z.read("bag-info.txt").decode()
    audit = (root / "logs/audit.jsonl").read_text(encoding="utf-8")
    assert "vault_add" in audit and "vault_backup" in audit


def test_vault_is_never_committed():
    from pathlib import Path
    gi = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "workspace/" in gi


# ------------------------------------------------------------------ مهارات Claude Code
def test_skills_gen_covers_available_skills_and_is_fresh():
    from rkpos import registry as R
    files = skillgen.build()
    avail = [s for s in R.skills().values() if s["status"] == "available_now"]
    assert len(files) == len(avail) and avail
    for p, text in files.items():
        head = yaml.safe_load(text.split("---")[1])
        assert head["name"] == p.parent.name and head["name"].startswith("bahith-")
        assert head["description"].startswith("استدعِ هذه المهارة")
        assert "## الإجراء" in text and "## المخرجات" in text and "## طريقة التحقق" in text
        assert "## الدستور المشترك" in text and "صفر تلفيق" in text
    assert skillgen.generate(check=True) == [], "شغّلوا rkpos skills-gen"


# ------------------------------------------------------------------ التثليث واستقلال الأصول
SRCS = [
    {"Source_ID": "SRC-000001", "Source_Type": "reputable_journalism", "Tier": 4, "Origin": "وكالة الأنباء"},
    {"Source_ID": "SRC-000002", "Source_Type": "reputable_journalism", "Tier": 4, "Origin": "وكالة الأنباء"},
    {"Source_ID": "SRC-000003", "Source_Type": "general_web", "Tier": 5},
    {"Source_ID": "SRC-000004", "Source_Type": "peer_reviewed_journal", "Tier": 1},
    {"Source_ID": "SRC-000005", "Source_Type": "government_record", "Tier": 1},
]


def _c(cid, status, *ids, **ref):
    return {"claim_id": cid, "project_id": "RKP-2026-0001", "location": "U1", "text": "…", "tag": "FACT",
            "status": status, "sources": [{"source_id": i, **ref} for i in ids]}


def test_shared_origin_counts_once():
    t = claims.triangulation(_c("C-0001", "PARTIAL", "SRC-000001", "SRC-000002"), SRCS)
    assert t["supporting_sources"] == 2 and t["independent_origins"] == 1 and t["dependent_links"] == 1
    assert t["shared_origins"] and t["press_only"] and t["flags"] == []     # غير معتمد: لا تنبيه


def test_established_press_only_and_single_origin_flagged():
    t = claims.triangulation(_c("C-0002", "SUPPORTED", "SRC-000001", "SRC-000002", "SRC-000003"), SRCS)
    assert t["independent_origins"] == 2 and t["press_only"] and "press_only" in t["flags"]
    assert t["types_count"] == 2 and "صحافة موثوقة" in t["type_labels"]
    t = claims.triangulation(_c("C-0003", "SUPPORTED", "SRC-000004"), SRCS)
    assert t["flags"] == ["single_origin"] and t["best_tier"] == 1
    t = claims.triangulation(_c("C-0004", "SUPPORTED", "SRC-000004", "SRC-000005"), SRCS)
    assert t["flags"] == [] and t["independent_origins"] == 2 and t["types_count"] == 2
    # أصل مشترك يُعلن في إحالة الادعاء نفسها
    t = claims.triangulation(_c("C-0005", "SUPPORTED", "SRC-000004", "SRC-000005", origin="تقرير واحد"), SRCS)
    assert t["independent_origins"] == 1 and "single_origin" in t["flags"]
    t = claims.triangulation(_c("C-0006", "SUPPORTED"), SRCS)
    assert t["flags"] == ["no_sources"]


def test_triangulate_summary_and_command(sandbox):
    rep = claims.triangulate([_c("C-0001", "SUPPORTED", "SRC-000001", "SRC-000003"),
                              _c("C-0002", "SUPPORTED", "SRC-000004", "SRC-000005"),
                              _c("C-0003", "UNCHECKED", "SRC-000777")], SRCS)
    s = rep["summary"]
    assert s["claims"] == 3 and s["established"] == 2 and s["press_only_established"] == 1
    assert s["unknown_sources"] == ["SRC-000777"] and not s["passes"] and len(rep["flagged"]) == 2

    pid = yaml.safe_load(sandbox("new-project", "مقال", "--type", "op_ed").stdout)["project_id"]
    root = sandbox.root / "projects" / pid
    src = {"Source_ID": "SRC-000001", "Title": "خبر", "Author": ["محرر"], "Year": 2025, "Source_Type": "reputable_journalism",
           "Peer_Reviewed": False, "Verification_Status": "PARTIAL", "Reliability_Level": "MEDIUM", "Date_Accessed": "2026-10-01",
           "Origin": "وكالة الأنباء"}
    (root / "research/sources.jsonl").write_text(json.dumps(src, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "evidence/claims.jsonl").write_text(json.dumps(_c("C-0001", "SUPPORTED", "SRC-000001"), ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    r = sandbox("triangulate", pid, ok=False)
    out = yaml.safe_load(r.stdout)
    assert r.returncode == 2 and out["summary"]["press_only_established"] == 1
    assert "معتمد يستند إلى الصحافة أو الويب وحدهما" in out["flagged"][0]["flags_ar"]
    from rkpos import registry as R
    assert R.validate(src, "source") == []          # الحقل Origin مقبول في مخطط المصدر


# ------------------------------------------------------------------ خط أساس المؤشرات
def test_kpi_baseline_is_human_decision(sandbox):
    out = yaml.safe_load(sandbox("kpis").stdout)
    assert out["note"] == "لا تُعتمد مستهدفات رقمية قبل تأسيس خط أساس تجريبي"
    sandbox("dashboard")
    html = (sandbox.root / "publishing/dashboard/index.html").read_text(encoding="utf-8")
    assert "لا تُعتمد مستهدفات رقمية قبل تأسيس خط أساس تجريبي" in html and "مؤشرات المؤسسة" in html

    bad = sandbox("kpis", "--set-baseline", "--actor", "AG-ORC", ok=False)
    assert bad.returncode != 0 and not (sandbox.root / "logs/kpi_baseline.json").exists()
    sandbox("new-project", "مقال", "--type", "op_ed")
    b = yaml.safe_load(sandbox("kpis", "--set-baseline", "--actor", "HUMAN-AUTHOR", "--decision", "خط أساس التجربة").stdout)
    assert b["by"] == "HUMAN-AUTHOR" and b["values"]["projects"] == 1
    sandbox("new-project", "مقال ثان", "--type", "op_ed")
    out = yaml.safe_load(sandbox("kpis").stdout)
    assert "note" not in out and out["baseline_at"]
    proj = next(i for i in out["items"] if i["label"] == "المشاريع")
    assert proj["value"] == 2 and proj["baseline"] == 1 and proj["delta"] == 1
    audit = [json.loads(l) for l in (sandbox.root / "logs/audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(a["ACTION"] == "kpi_baseline" and a["DECISION_LEVEL"] == "L4" for a in audit)
    sandbox("dashboard")
    html = (sandbox.root / "publishing/dashboard/index.html").read_text(encoding="utf-8")
    assert "خط الأساس" in html and "لا تُعتمد مستهدفات" not in html
