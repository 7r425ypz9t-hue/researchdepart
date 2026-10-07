"""rkpos — واجهة سطر الأوامر لوحدة «مِداد».

أمثلة:
  rkpos validate
  rkpos generate [--check]
  rkpos new-project "حوكمة الذكاء الاصطناعي في القطاع الثقافي" --type intellectual_book --domain cultural_governance
  rkpos status RKP-2026-0001
  rkpos run-step RKP-2026-0001 [--step S02] [--live]
  rkpos record-output RKP-2026-0001 S02 path/to/output.md
  rkpos complete RKP-2026-0001 S02 --actor HUMAN-AUTHOR --decision "اعتماد السؤال الرئيس والنطاق"
  rkpos prompt AG-WRT
  rkpos verify-doi 10.xxxx/yyyy --title "..."
  rkpos check-manuscript RKP-2026-0001 path/to/chapter.md
  rkpos select --type policy_study --model B --domain cultural_policy --risk high
  rkpos cost-report [--project RKP-...]
  rkpos dashboard
  rkpos eval AG-WRT [--live]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import yaml


def _p(obj):
    print(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False) if not isinstance(obj, str) else obj)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rkpos", description="MIDAD Research & Knowledge Production OS")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="فحص سلامة المنظومة (المخططات والإحالات والصلاحيات)")
    g = sub.add_parser("generate", help="توليد ملفات الوكلاء والمصفوفات")
    g.add_argument("--check", action="store_true")

    n = sub.add_parser("new-project")
    n.add_argument("title")
    n.add_argument("--type", required=True)
    n.add_argument("--domain")
    n.add_argument("--model", default="A", choices=["A", "B", "C"])
    n.add_argument("--has-data", action="store_true")
    n.add_argument("--risk", default="medium")
    n.add_argument("--evidence", default="standard")
    n.add_argument("--target")
    n.add_argument("--deadline")
    n.add_argument("--grmm", help="مسار GRMM الحاكم إن وُجد")

    s = sub.add_parser("status"); s.add_argument("project")
    r = sub.add_parser("run-step"); r.add_argument("project"); r.add_argument("--step"); r.add_argument("--live", action="store_true")
    ro = sub.add_parser("record-output"); ro.add_argument("project"); ro.add_argument("step"); ro.add_argument("file")
    c = sub.add_parser("complete"); c.add_argument("project"); c.add_argument("step"); c.add_argument("--actor", required=True)
    c.add_argument("--decision"); c.add_argument("--approved-file")
    pr = sub.add_parser("prompt"); pr.add_argument("agent"); pr.add_argument("--register", choices=["essay", "narrative", "academic"])
    vd = sub.add_parser("verify-doi"); vd.add_argument("doi"); vd.add_argument("--title"); vd.add_argument("--year", type=int)
    cm = sub.add_parser("check-manuscript"); cm.add_argument("project"); cm.add_argument("file")
    se = sub.add_parser("select"); se.add_argument("--type", required=True); se.add_argument("--model", default="A")
    se.add_argument("--domain"); se.add_argument("--has-data", action="store_true"); se.add_argument("--risk", default="medium")
    se.add_argument("--evidence", default="standard"); se.add_argument("--target")
    sp = sub.add_parser("style-profile", help="قياس البصمة الأسلوبية لنص ومقارنته بملف مرجعي")
    sp.add_argument("file"); sp.add_argument("--reference", help="اسم الملف المرجعي في memory/author/private (مثل essay)")
    cr = sub.add_parser("cost-report"); cr.add_argument("--project")
    sub.add_parser("dashboard")
    ev = sub.add_parser("eval"); ev.add_argument("agent", nargs="?"); ev.add_argument("--live", action="store_true")
    mp = sub.add_parser("memory-promote"); mp.add_argument("memory_id"); mp.add_argument("--layer", required=True); mp.add_argument("--approved-by", required=True)

    a = ap.parse_args(argv)

    if a.cmd == "validate":
        from . import registry, generate
        errs = registry.check_integrity()
        stale = generate.write(check=True)
        errs += [f"stale generated file: {p}" for p in stale]
        if errs:
            _p("\n".join(errs)); return 1
        _p("✓ المنظومة متسقة: الوكلاء والمهارات والأدوات والذاكرة وسير العمل والبوابات والملفات المولدة.")
        return 0
    if a.cmd == "generate":
        from . import generate
        changed = generate.write(check=a.check)
        if a.check and changed:
            _p("stale:\n" + "\n".join(map(str, changed))); return 1
        _p(f"{len(changed)} file(s) {'stale' if a.check else 'written'}"); return 0
    if a.cmd == "new-project":
        from . import project
        m = project.new_project(a.title, a.type, domain=a.domain, operating_model=a.model, has_data=a.has_data, risk=a.risk,
                                evidence_requirement=a.evidence, publication_target=a.target, deadline=a.deadline, governing_manifest=a.grmm)
        _p({"project_id": m["project_id"], "workflow": m["workflow"], "agents": m["agents"], "next": "rkpos run-step " + m["project_id"]})
        return 0
    if a.cmd == "status":
        from . import state
        _p(state.load(a.project)); return 0
    if a.cmd == "run-step":
        from . import runner
        _p(f"→ {runner.run_step(a.project, a.step, live=a.live)}"); return 0
    if a.cmd == "record-output":
        from . import runner
        _p(f"→ {runner.record_output(a.project, a.step, Path(a.file))}"); return 0
    if a.cmd == "complete":
        from . import runner
        _p(runner.complete(a.project, a.step, a.actor, a.decision, Path(a.approved_file) if a.approved_file else None)); return 0
    if a.cmd == "prompt":
        from . import runner
        print(runner.compose_system_prompt(a.agent, a.register)); return 0
    if a.cmd == "verify-doi":
        from .verify import doi
        _p(doi.verify(a.doi, a.title, a.year)); return 0
    if a.cmd == "check-manuscript":
        from .paths import PROJECTS
        from .verify import citations, claims, sources, terms
        text = Path(a.file).read_text(encoding="utf-8")
        srcs = sources.load(PROJECTS / a.project / "research/sources.jsonl") + sources.load()
        rep = {"claims": claims.audit(text), "citations": citations.audit(text, srcs), "terminology": terms.check(text)}
        from . import stylometry
        reg = stylometry.register_for(a.project)
        ref = stylometry.load_reference(reg)
        if ref:  # تنبيه أسلوبي لا يحجب البوابة (القرار للمحرر والمؤلف)
            prof = stylometry.profile(text)
            rep["style_deviation"] = stylometry.distance(prof, ref)
            assisted = stylometry.load_assisted_pole()
            if assisted and reg in stylometry.POLE_REGISTERS:
                rep["voice_pole"] = stylometry.pole(prof, ref, assisted)
        _p(rep); return 0 if rep["claims"]["passes"] and rep["citations"]["passes_qg4"] else 2
    if a.cmd == "select":
        from . import selection
        _p(selection.select({"project_type": a.type, "operating_model": a.model, "domain": a.domain, "has_data": a.has_data,
                             "risk": a.risk, "evidence_requirement": a.evidence, "publication_target": a.target})); return 0
    if a.cmd == "style-profile":
        from . import stylometry
        prof = stylometry.profile(Path(a.file).read_text(encoding="utf-8"))
        prof.pop("top_bigrams", None)
        out = {"profile": prof}
        if a.reference:
            ref = stylometry.load_reference(a.reference)
            out["deviation"] = stylometry.distance(prof, ref) if ref else f"no reference '{a.reference}' in memory/author/private/"
            assisted = stylometry.load_assisted_pole()
            if ref and assisted and a.reference in stylometry.POLE_REGISTERS:
                out["voice_pole"] = stylometry.pole(prof, ref, assisted)
        _p(out); return 0
    if a.cmd == "cost-report":
        from . import cost
        _p(cost.report(a.project)); return 0
    if a.cmd == "dashboard":
        from . import dashboard
        _p(f"→ {dashboard.build()}"); return 0
    if a.cmd == "eval":
        from . import evals, registry
        ids = [a.agent] if a.agent else list(registry.agents())
        if a.live:
            for i in ids:
                print(json.dumps(evals.live_run(i), ensure_ascii=False, indent=2))
            return 0
        errs = [e for i in ids for e in evals.offline_check(i)]
        _p("\n".join(errs) if errs else f"✓ {len(ids)} test suite(s) structurally valid"); return 1 if errs else 0
    if a.cmd == "memory-promote":
        from . import knowledge
        _p(knowledge.promote(a.memory_id, a.layer, a.approved_by)); return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
