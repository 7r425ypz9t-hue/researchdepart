import pytest

from rkpos import protocol as P, registry as R


def test_handoff_without_context_rejected():
    with pytest.raises(P.ProtocolError):
        P.handoff("RKP-2026-0001", "AG-WRT", "AG-EVA", "audit chapter 1", "", [], [], [], [],
                  {"status": "PENDING"}, "2026-12-31", "fact audit")


def test_valid_handoff():
    h = P.handoff("RKP-2026-0001", "AG-WRT", "AG-EVA", "audit chapter 1",
                  "الفصل الأول من كتاب الحوكمة الثقافية؛ المسودة v0.1 موسومة بالكامل.", ["drafts/ch01_v0.1.md"],
                  ["DC-001: الأطروحة المعتمدة"], [], ["SRC-000001"], {"status": "PENDING", "open_issues": 0},
                  "2026-12-31", "fact_audit_ch01.yaml")
    assert h["HANDOFF_ID"].startswith("HO-")


def test_unauthorized_route_rejected():
    # وكيل النشر لا يرسل مهمة إلى الكاتب مباشرة
    with pytest.raises(P.ProtocolError):
        P.message("RKP-2026-0001", "TASK", "AG-PUB", "AG-WRT", "rewrite", "x", "rewrite chapter")


def test_reject_requires_evidence():
    with pytest.raises(P.ProtocolError):
        P.message("RKP-2026-0001", "REJECT", "AG-SUP-INT", "AG-ORC", "QG4 rejected", "fabricated ref", "fix")
    m = P.message("RKP-2026-0001", "REJECT", "AG-SUP-INT", "AG-ORC", "QG4 rejected", "fabricated ref", "fix",
                  evidence=["SRC-000009: FAILED"])
    assert m["TYPE"] == "REJECT"


def test_source_schema_forbids_unverified_doi():
    rec = {"Source_ID": "SRC-000001", "Title": "T", "Author": ["A"], "Year": 2020, "DOI": "10.1234/abc",
           "Date_Accessed": "2026-10-07", "Source_Type": "peer_reviewed_journal", "Peer_Reviewed": True,
           "Verification_Status": "UNVERIFIED", "Reliability_Level": "UNKNOWN"}
    assert R.validate(rec, "source")
    rec.update(Verification_Status="VERIFIED", Verification_Evidence={"tool": "TL-CROSSREF", "checked_at": "x"})
    assert R.validate(rec, "source") == []


def test_memory_schema_requires_author_approval_for_institutional():
    item = {"Memory_ID": "MEM-LESSON-000001", "Type": "lesson", "Layer": "MEM-INSTITUTIONAL", "Project": None,
            "Created_By": "AG-KNW", "Created_Date": "2026-10-07", "Verified": True, "Confidence": "HIGH", "Source": "DC-003",
            "Version": 1, "Access_Level": "INTERNAL", "Content": "درس", "Approved_By": "AG-DIR"}
    assert R.validate(item, "memory_item")
    item["Approved_By"] = "HUMAN-AUTHOR"
    assert R.validate(item, "memory_item") == []


def test_claim_schema_fact_needs_source():
    c = {"claim_id": "C-0001", "project_id": "RKP-2026-0001", "location": "ch1:p3", "text": "x", "tag": "FACT", "status": "UNCHECKED"}
    assert R.validate(c, "claim")
    c["sources"] = [{"source_id": "SRC-000001", "locator": "p. 4"}]
    assert R.validate(c, "claim") == []


def test_templates_validate_against_schemas():
    import json
    from pathlib import Path
    import yaml
    t = Path(__file__).resolve().parents[1] / "templates"
    assert R.validate(json.loads((t / "handoff.example.json").read_text(encoding="utf-8")), "handoff") == []
    assert R.validate(json.loads((t / "message.example.json").read_text(encoding="utf-8")), "message") == []
    assert R.validate(json.loads((t / "source_record.example.json").read_text(encoding="utf-8")), "source") == []
    assert R.validate(json.loads((t / "memory_item.example.json").read_text(encoding="utf-8")), "memory_item") == []
    assert R.validate(json.loads((t / "audit.example.json").read_text(encoding="utf-8")), "audit") == []
    assert R.validate(yaml.safe_load((t / "project_manifest.template.yaml").read_text(encoding="utf-8")), "project_manifest") == []
    assert R.validate(yaml.safe_load((t / "gate_decision.template.yaml").read_text(encoding="utf-8")), "gate_decision") == []


def test_author_only_items_never_touch_tracked_files(tmp_path, monkeypatch):
    from rkpos import knowledge as K, audit
    monkeypatch.setattr(K, "CANDIDATES", tmp_path / "public/candidates.jsonl")
    monkeypatch.setattr(K, "PRIVATE_CANDIDATES", tmp_path / "private/candidates.jsonl")
    monkeypatch.setattr(K, "LAYER_FILES", {**K.LAYER_FILES, "MEM-AUTHOR": tmp_path / "private/items.jsonl"})
    monkeypatch.setattr(K, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "LOGS", tmp_path / "logs")
    item = {"Memory_ID": "MEM-STYLE-999999", "Type": "style_rule", "Project": None, "Created_By": "AG-KNW",
            "Created_Date": "2026-10-07", "Confidence": "HIGH", "Source": "test", "Version": 1,
            "Access_Level": "AUTHOR_ONLY", "Content": "سر"}
    K.propose(item)
    assert not (tmp_path / "public/candidates.jsonl").exists()
    with pytest.raises(PermissionError):
        K.promote("MEM-STYLE-999999", "MEM-AUTHOR", "AG-KNW")
    with pytest.raises(PermissionError):
        K.promote("MEM-STYLE-999999", "MEM-INSTITUTIONAL", "HUMAN-AUTHOR")
    K.promote("MEM-STYLE-999999", "MEM-AUTHOR", "HUMAN-AUTHOR")
    assert (tmp_path / "private/items.jsonl").exists()
    assert "سر" not in (tmp_path / "logs/audit.jsonl").read_text(encoding="utf-8")
