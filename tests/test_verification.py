from rkpos.verify import doi, citations, claims, bibclean, terms
from rkpos import gates, selection


def _fake(msg):
    return lambda d: msg


def test_doi_verified_on_title_match():
    msg = {"title": ["Cultural Policy and Governance"], "issued": {"date-parts": [[2019]]}, "author": [{"given": "A", "family": "B"}]}
    r = doi.verify("https://doi.org/10.1234/ABC", "Cultural policy and governance", 2019, fetcher=_fake(msg))
    assert r["status"] == "VERIFIED" and r["metadata"]["DOI"] == "10.1234/abc"


def test_doi_not_found_fails():
    assert doi.verify("10.9999/fake.2024.001", fetcher=_fake(None))["status"] == "FAILED"


def test_doi_network_error_is_pending_not_failed():
    def boom(d):
        raise OSError("offline")
    assert doi.verify("10.1234/abc", fetcher=boom)["status"] == "PENDING"


def test_doi_title_mismatch_partial():
    msg = {"title": ["Something entirely different"], "issued": {"date-parts": [[2019]]}}
    assert doi.verify("10.1234/abc", "Cultural policy", fetcher=_fake(msg))["status"] == "PARTIAL"


def test_doi_retraction_detected():
    msg = {"title": ["X"], "update-to": [{"type": "retraction"}]}
    assert doi.verify("10.1234/abc", fetcher=_fake(msg))["status"] == "RETRACTED"


def test_malformed_doi():
    assert doi.verify("not-a-doi", fetcher=_fake({}))["status"] == "FAILED"


SOURCES = [
    {"Source_ID": "SRC-000001", "Verification_Status": "VERIFIED", "Tier": 1, "Title": "A", "Year": 2020},
    {"Source_ID": "SRC-000002", "Verification_Status": "FAILED", "Tier": 1, "Title": "B", "Year": 2021},
]


def test_citation_audit_blocks_failed_and_missing():
    rep = citations.audit("نص [@SRC-000001, p. 3] و[@SRC-000002] و[@SRC-000777]", SOURCES)
    assert rep["missing"] == ["SRC-000777"] and rep["blocking"] == ["SRC-000002:FAILED"] and not rep["passes_qg4"]


def test_claim_audit():
    text = "[FACT] الاتفاقية أُقرت عام 2005 [@SRC-000001].\n\n[INTERP] وهذا يعني تحولاً.\n\nفقرة بلا وسم.\n\n[FACT] رقم بلا مصدر."
    rep = claims.audit(text)
    assert rep["untagged"] == [3] and rep["fact_without_source"] == [4] and not rep["passes"]


def test_bibclean_arabic_normalization():
    recs = [{"Source_ID": "SRC-000001", "Title": "إدارة الثقافة", "Year": 2010},
            {"Source_ID": "SRC-000002", "Title": "ادارة الثقافه", "Year": 2010}]
    assert bibclean.duplicates(recs) == [("SRC-000001", "SRC-000002", "title+year")]


def test_terms():
    hits = terms.check("الحوكمه الثقافيه", [{"ar": "الحوكمة الثقافية", "avoid": ["الحوكمه الثقافيه"]}])
    assert hits and hits[0]["preferred"] == "الحوكمة الثقافية"


def test_qg1_auto_checks():
    res = gates.auto_checks("QG1", SOURCES)
    assert any(r["result"] == "FAIL" for r in res)


def test_selection_minimal_for_oped():
    s = selection.select({"project_type": "op_ed", "operating_model": "A"})
    ids = {a for v in s["agents"].values() for a in v}
    assert ids == {"AG-ORC", "AG-DSC", "AG-SRC", "AG-WRT", "AG-SED", "AG-INT", "AG-PUB", "AG-KNW"}


def test_selection_policy_high_risk_model_b():
    s = selection.select({"project_type": "policy_study", "operating_model": "B", "domain": "cultural_policy", "risk": "high"})
    ids = {a for v in s["agents"].values() for a in v}
    assert {"AG-POL", "AG-CUL", "AG-RED", "AG-SUP-INT"} <= ids


def test_qg3_blocks_open_critical_challenge():
    res = gates.auto_checks("QG3", [], red_team=[{"id": "RT-001", "severity": "critical", "status": "OPEN"},
                                                  {"id": "RT-002", "severity": "low", "status": "OPEN"}])
    assert res[-1]["result"] == "FAIL" and res[-1]["evidence"] == "RT-001"
