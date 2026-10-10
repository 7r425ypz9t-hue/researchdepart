"""إنشاء المشروع: Project ID → Manifest → اختيار الوكلاء → المجلدات → الخطة → الحالة → السجل."""
from __future__ import annotations
import datetime as dt

import yaml

from . import audit, registry as R, selection, workflow as WF
from .ids import next_project_id, slugify, now_iso
from .paths import PROJECTS, CONFIG

PROJECT_DIRS = ["memory", "research", "evidence", "data/raw", "data/derived", "manuscript/drafts", "manuscript/edited",
                "manuscript/approved", "reviews", "archive", "watch", "messages", "runs", "figures", "tables"]

DEFAULT_DELIVERABLES = {
    "intellectual_book": ["مخطوط كامل معتمد", "PDF للطباعة", "EPUB", "بيانات وصفية", "سجل المشروع"],
    "academic_book": ["مخطوط محكّم", "PDF", "EPUB", "فهارس", "ببليوغرافيا"],
    "policy_study": ["ورقة سياسات", "ملخص تنفيذي", "توصيات"],
    "op_ed": ["مقال رأي ≤ 300 كلمة"],
    "novel": ["كرّاسة الرواية", "مخطوط الرواية المعتمد", "PDF/EPUB", "سجل المشروع"],
    "novella": ["كرّاسة العمل", "مخطوط معتمد", "سجل المشروع"],
    "short_story": ["قصة معتمدة", "سجل المشروع"],
    "essay_collection": ["مخطوط المجموعة المعتمد", "PDF", "EPUB", "سجل المشروع"],
    "play": ["كرّاسة المسرحية", "نص المسرحية المعتمد", "سجل المشروع"],
    "economic_study": ["دراسة معتمدة", "ملخص تنفيذي", "إطار المؤشرات", "سجل المشروع"],
    "cultural_study": ["دراسة معتمدة", "ملخص تنفيذي", "إطار المؤشرات", "سجل المشروع"],
    "development_study": ["دراسة معتمدة", "ملخص تنفيذي", "توصيات", "سجل المشروع"],
}


def new_project(title: str, project_type: str, author: str = "د. ماجد بوشليبي", domain: str | None = None,
                operating_model: str = "A", has_data: bool = False, risk: str = "medium",
                evidence_requirement: str = "standard", publication_target: str | None = None,
                deadline: str | None = None, citation_style: str | None = None,
                governing_manifest: str | None = None, genre: str | None = None,
                production_level: str | None = None, target_pages: int | None = None,
                words_per_page: int | None = None) -> dict:
    from . import genres as GN, institution
    genre = GN.genre_for_type(project_type, genre)
    production_level = production_level or ("full" if genre == "op_ed" else "staged")
    GN.check_level(genre, production_level)
    pid = next_project_id()
    root = PROJECTS / pid
    for d in PROJECT_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    ctx = {"project_type": project_type, "operating_model": operating_model, "domain": domain, "has_data": has_data,
           "risk": risk, "evidence_requirement": evidence_requirement, "publication_target": publication_target}
    sel = selection.select(ctx)
    wid = WF.workflow_for(project_type)
    wf = R.workflows()[wid]
    gstyle = GN.genres()[genre]["citation_style"]
    style = citation_style or ("none" if gstyle == "none" else
                               {"Chicago": "Chicago", "APA7": "APA7"}.get(wf.get("citation_style"), gstyle))
    budget = R.load_yaml(CONFIG / "cost_limits.yaml")["defaults_by_project_type"].get(project_type)

    manifest = {
        "project_id": pid, "slug": slugify(title), "title": title, "title_status": "WORKING",
        "project_type": project_type, "genre": genre, "division": institution.division_for_type(project_type), "workflow": wid, "operating_model": operating_model, "author": author,
        "governing_manifest": governing_manifest,
        "objectives": ["(تُستكمل في S02 بواسطة AG-RQA وتُعتمد عند QG0)"],
        "thesis": None,
        "research_questions": {"main": None, "sub": []},
        "scope": {"in": [], "out": [], "period": None, "geography": None},
        "methodology": None,
        "agents": {k: sel["agents"].get(k, []) for k in ("core", "specialist", "supervisory", "utility", "on_demand")},
        "selection_rationale": sel["rationale"],
        "classification": ctx,
        "sources_policy": {"hierarchy": "governance/source_hierarchy.yaml", "zero_fabrication": True,
                           "min_tier12_share_central": 0.7, "min_verified_ratio": 0.95},
        "citation_style": style, "language": "ar",
        "deliverables": DEFAULT_DELIVERABLES.get(project_type, ["المخرج الرئيس", "سجل المشروع"]),
        "quality_gates": ["QG0", "QG1", "QG2", "QG3", "QG4", "QG5", "QG6", "QG7"],
        "human_approvals": ["العنوان", "الأطروحة", "الهيكل", "الاستنتاجات الجوهرية", "النشر النهائي"],
        "production": {"level": production_level, "target_pages": target_pages,
                       "words_per_page": words_per_page or GN.levels()["words_per_page_default"],
                       "target_words": GN.genres()[genre].get("max_words") or
                       (target_pages * (words_per_page or GN.levels()["words_per_page_default"]) if target_pages else None)},
        "budget_usd": budget, "deadline": deadline, "data_classification": "CONFIDENTIAL",
        "status": "ACTIVE", "version": "v0.1", "created": now_iso(),
    }
    errs = R.validate(manifest, "project_manifest")
    if errs:
        raise ValueError(errs)
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")

    steps = WF.expand(wid, {"project": ctx})
    active = {a for v in sel["agents"].values() for a in v} | {"AG-ORC", "HUMAN-AUTHOR", "AG-COUNCIL"}
    for s in steps:
        if s.get("agent") and s["agent"] not in active and s["status"] != "SKIPPED":
            sub = R.load_yaml(R.ROOT / "validation/agent_selection_rules.yaml")["model_substitutions"].get(s["agent"])
            s["assigned_agent"] = sub if sub in active else s["agent"]
            if sub in active:
                s["note"] = f"{s['agent']} غير مفعّل في هذا النموذج؛ تُنفذ المهمة بمهارة داخل {sub}"
            else:
                s["assigned_agent"] = "AG-ORC"
                s["note"] = f"{s['agent']} غير مفعّل؛ يقرر المنسق: تنفيذ بمهارة قائمة أو تفعيل عبر WF-MISSING-AGENT"
        if s.get("agent") == "AG-COUNCIL" and operating_model == "A":
            s["assigned_agent"] = "HUMAN-AUTHOR"
    (root / "plan.yaml").write_text(yaml.safe_dump({"project_id": pid, "workflow": wid, "steps": steps},
                                                   allow_unicode=True, sort_keys=False), encoding="utf-8")
    (root / "decisions.yaml").write_text(yaml.safe_dump({"project_id": pid, "decisions": []}, allow_unicode=True), encoding="utf-8")
    (root / "outline.yaml").write_text("chapters: []\nfigures_plan: []\n", encoding="utf-8")
    from . import book
    book.init(pid, production_level, target_pages, words_per_page, genre)
    (root / "evidence/claims.jsonl").touch()
    (root / "research/sources.jsonl").touch()
    (root / "CHANGELOG.md").write_text(f"# CHANGELOG — {pid}\n\n## v0.1 Draft — {dt.date.today()}\n- فتح المشروع «{title}» وفق {wid}.\n", encoding="utf-8")

    first = WF.expand(wid, {"project": ctx})[0]
    state = {"PROJECT_ID": pid, "STATE": "INITIALIZED", "STAGE_ID": first["id"],
             "NEXT_ACTION": "S02", "CURRENT_AGENT": "AG-ORC",
             "WAITING_FOR": None, "BLOCKERS": [], "VERSION": "v0.1", "QUALITY_GATE": {"current": "QG0", "status": "PENDING"},
             "COMPLETION_PCT": 0, "LAST_WORK_POINT": "initialize_project", "PINNED_DECISIONS": [],
             "PENDING_HUMAN_DECISIONS": [], "OPEN_ISSUES": 0, "COST_USD": 0.0, "DEADLINE": deadline, "UPDATED": now_iso()}
    from . import state as ST
    ST.save(pid, state)
    # S01 initialize_project منجز بإنشاء المشروع
    p = ST.plan(pid)
    p["steps"][0]["status"] = "DONE"
    ST.save_plan(pid, p)
    ST.refresh(pid)
    audit.log("AG-ORC", "initialize_project", project=pid,
              files_changed=[f"projects/{pid}/{f}" for f in ("manifest.yaml", "state.yaml", "plan.yaml", "decisions.yaml", "CHANGELOG.md")],
              decision=f"workflow={wid}; agents={sorted(active - {'HUMAN-AUTHOR', 'AG-COUNCIL'})}", decision_level="L1")
    return manifest
