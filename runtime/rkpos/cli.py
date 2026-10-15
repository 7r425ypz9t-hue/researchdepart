"""rkpos — واجهة سطر الأوامر لمؤسسة «باحث».

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
  rkpos run-step RKP-2026-0001 --live --engine claude_code
  rkpos activate AG-WRT "اكتب مسودة عمود عن…" [--register essay] [--project RKP-…] [--engine claude_code]
  rkpos panel                 # لوحة التحكم المحلية
  rkpos install-icon [--remove]
  rkpos icon set صورة.png | rkpos icon reset | rkpos icon status   # أيقونة يعتمدها المؤلف
  rkpos fonts install adwa-assalaf.ttf adwa-assalaf_B.ttf | rkpos fonts system | rkpos fonts status | rkpos fonts remove
  rkpos vault add path/to/file.pdf [--project RKP-…] [--provenance "…"] [--rights "…"]
  rkpos vault verify | rkpos vault list [--project RKP-…]
  rkpos backup [--out مجلد]
  rkpos skills-gen [--check]   # مهارات Claude Code في .claude/skills
  rkpos triangulate RKP-2026-0001
  rkpos kpis [--set-baseline --actor HUMAN-AUTHOR --decision "…"]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

import yaml


def _p(obj):
    print(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False) if not isinstance(obj, str) else obj)


def load_env() -> None:
    """يقرأ .env من جذر المستودع (غير متتبع) دون أن يطغى على متغيرات البيئة القائمة."""
    from .paths import ROOT
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if v[:1] in ("'", '"') and v[-1:] == v[:1]:
            v = v[1:-1]
        else:
            v = v.split(" #", 1)[0].strip()
        if v and k.strip() not in os.environ:
            os.environ[k.strip()] = v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rkpos", description="Bahith — Research & Knowledge Development Institution")
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
    n.add_argument("--genre", choices=["creative", "research", "intellectual", "op_ed"], help="يُشتق من النوع إن لم يُذكر")
    n.add_argument("--level", choices=["scaffold", "staged", "full"], help="مستوى الإنتاج")
    n.add_argument("--pages", type=int, help="عدد الصفحات المستهدف")
    n.add_argument("--words-per-page", type=int)
    bk = sub.add_parser("book", help="بناء العمل: المخطط والوحدات والصوت والتجميع")
    bk.add_argument("project")
    bk.add_argument("action", choices=["show", "skeleton", "propose-outline", "approve-outline", "draft", "draft-all",
                                       "record", "align", "approve", "assemble", "voice", "estimate"])
    bk.add_argument("unit", nargs="?"); bk.add_argument("--n", type=int, default=5); bk.add_argument("--file")
    bk.add_argument("--engine", default="manual", choices=["auto", "claude_code", "api", "manual"])
    bk.add_argument("--actor", default=None)

    s = sub.add_parser("status"); s.add_argument("project")
    r = sub.add_parser("run-step"); r.add_argument("project"); r.add_argument("--step"); r.add_argument("--live", action="store_true")
    r.add_argument("--engine", choices=["auto", "claude_code", "api", "manual"], help="محرّك التشغيل الحي")
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
    au = sub.add_parser("autopilot", help="الطيار الآلي: الوكلاء يعملون تباعاً ويتوقفون عند قرار المؤلف")
    au.add_argument("project"); au.add_argument("--engine", default="claude_code", choices=["auto", "claude_code", "api"])
    au.add_argument("--answer", help="معرّف الخيار للإجابة عن السؤال القائم"); au.add_argument("--note", default="")
    au.add_argument("--status", action="store_true")
    au.add_argument("--mode", choices=["direct", "guided"], help="مباشر (الافتراضي): مسودة كاملة ثم مراجعتي؛ موجَّه: أعتمد كل مرحلة")
    ac = sub.add_parser("activate", help="تفعيل وكيل مباشرة بتكليف من المؤلف")
    ac.add_argument("agent"); ac.add_argument("task"); ac.add_argument("--register", choices=["essay", "narrative", "academic"])
    ac.add_argument("--project"); ac.add_argument("--context", default="")
    ac.add_argument("--engine", default="manual", choices=["auto", "claude_code", "api", "manual"])
    pa = sub.add_parser("panel", help="لوحة التحكم المحلية (127.0.0.1)")
    pa.add_argument("--port", type=int, default=0); pa.add_argument("--no-browser", action="store_true")
    pa.add_argument("--new", action="store_true", help="لا تُعِد استعمال لوحة تعمل مسبقاً")
    ic = sub.add_parser("install-icon", help="أيقونة «باحث» على سطح المكتب"); ic.add_argument("--remove", action="store_true")
    ai = sub.add_parser("icon", help="أيقونة البرنامج: set صورة.png · reset · status")
    ai.add_argument("action", choices=["set", "reset", "status"]); ai.add_argument("file", nargs="?")
    fo = sub.add_parser("fonts", help="خط الهوية «أضواء السلف»: install · system · status · remove")
    fo.add_argument("action", choices=["install", "system", "status", "remove"]); fo.add_argument("files", nargs="*")
    va = sub.add_parser("vault", help="خزنة الأصول: إيداع وفحص سلامة وقائمة")
    vs = va.add_subparsers(dest="vcmd", required=True)
    vaa = vs.add_parser("add"); vaa.add_argument("file"); vaa.add_argument("--project"); vaa.add_argument("--provenance", default="")
    vaa.add_argument("--rights", default=""); vaa.add_argument("--depositor", default="HUMAN-AUTHOR")
    vs.add_parser("verify")
    val_ = vs.add_parser("list"); val_.add_argument("--project")
    bu = sub.add_parser("backup", help="نسخة احتياطية للخزنة على نمط BagIt"); bu.add_argument("--out")
    sg = sub.add_parser("skills-gen", help="توليد مهارات Claude Code من سجل المهارات"); sg.add_argument("--check", action="store_true")
    tr = sub.add_parser("triangulate", help="تثليث الأدلة واستقلال أصولها في سجل ادعاءات المشروع"); tr.add_argument("project")
    kp = sub.add_parser("kpis", help="مؤشرات المؤسسة وخط الأساس")
    kp.add_argument("--set-baseline", action="store_true"); kp.add_argument("--actor"); kp.add_argument("--decision", default="")
    mp = sub.add_parser("memory-promote"); mp.add_argument("memory_id"); mp.add_argument("--layer", required=True); mp.add_argument("--approved-by", required=True)

    a = ap.parse_args(argv)
    load_env()

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
                                evidence_requirement=a.evidence, publication_target=a.target, deadline=a.deadline, governing_manifest=a.grmm,
                                genre=a.genre, production_level=a.level, target_pages=a.pages, words_per_page=a.words_per_page)
        _p({"project_id": m["project_id"], "genre": m["genre"], "production": m["production"], "workflow": m["workflow"],
            "agents": m["agents"], "next": "rkpos run-step " + m["project_id"]})
        return 0
    if a.cmd == "status":
        from . import state
        _p(state.load(a.project)); return 0
    if a.cmd == "run-step":
        from . import runner
        _p(f"→ {runner.run_step(a.project, a.step, live=a.live or bool(a.engine), engine=a.engine)}"); return 0
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
        if (PROJECTS / a.project / "manifest.yaml").exists():   # تثليث سجل الادعاءات: تنبيه لا يحجب البوابة
            rep["triangulation"] = claims.triangulate_project(a.project)["summary"]
        from . import stylometry
        reg = stylometry.register_for(a.project)
        from .genres import VOICE_REGISTERS, discipline_report
        ref = stylometry.load_reference(reg) if reg in VOICE_REGISTERS else None
        if reg and reg not in VOICE_REGISTERS:
            rep["discipline"] = discipline_report(text)
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
    if a.cmd == "autopilot":
        from . import autopilot as AP
        if a.status:
            _p(AP.load(a.project)); return 0
        if a.answer:
            q = AP.load(a.project).get("question") or {}
            AP.answer(a.project, q.get("id", ""), a.answer, a.note)
        ap = AP.run(a.project, a.engine, mode=a.mode)
        q = ap.get("question")
        if q:
            _p({"status": ap["status"], "question": q["title"], "prompt": q["prompt"], "body": q.get("body"), "file": q.get("file"),
                "choices": {c["id"]: c["label"] for c in q["choices"]},
                "answer_with": f"rkpos autopilot {a.project} --answer <id> [--note \"…\"]"})
        else:
            _p({"status": ap["status"]})
        return 0
    if a.cmd == "book":
        from . import book as B
        pid, act, uid = a.project, a.action, a.unit
        need = lambda: uid or (_ for _ in ()).throw(SystemExit("حدّد الوحدة"))  # noqa: E731
        if act == "show": _p(B.load(pid))
        elif act == "skeleton": _p(B.skeleton(pid, a.n))
        elif act == "propose-outline": r = B.propose_outline(pid, a.engine, a.n); print(r["text"]) if r.get("manual") else _p(r)
        elif act == "approve-outline": _p(B.approve_outline(pid, a.actor or ""))
        elif act == "draft": r = B.draft_unit(pid, need(), a.engine); print(r["text"]) if r.get("manual") else _p(r)
        elif act == "draft-all": _p(B.draft_all(pid, a.engine, lambda i, n, u: print(f"[{i}/{n}] {u or 'تم'}", flush=True)))
        elif act == "record": _p(B.record_unit(pid, need(), Path(a.file).read_text(encoding="utf-8"), source="ai"))
        elif act == "align": _p(B.align_voice(pid, need(), a.engine))
        elif act == "approve": _p(B.approve_unit(pid, need(), a.actor or "", Path(a.file).read_text(encoding="utf-8") if a.file else None))
        elif act == "assemble": _p(B.assemble(pid))
        elif act == "voice": _p(B.voice_report(pid))
        elif act == "estimate": _p(B.estimate(pid))
        return 0
    if a.cmd == "activate":
        from . import runner
        r = runner.run_adhoc(a.agent, a.task, register=a.register, project=a.project, context=a.context, engine=a.engine)
        if r["output"]:
            print(r["output"])
        _p({k: r[k] for k in ("run_id", "dir", "model", "warnings", "usd")}); return 0
    if a.cmd == "panel":
        from .panel import server
        server.serve(port=a.port, open_browser=not a.no_browser, reuse=not a.new); return 0
    if a.cmd == "install-icon":
        from .panel import desktop
        _p({"installed" if not a.remove else "removed": desktop.install(remove=a.remove)}); return 0
    if a.cmd == "icon":
        from . import appicon
        from .panel import desktop
        out = {}
        if a.action == "set":
            if not a.file:
                raise SystemExit("حدّدوا صورة الأيقونة: rkpos icon set icon.png")
            appicon.adopt(Path(a.file).read_bytes())
        elif a.action == "reset":
            appicon.reset()
        if a.action in ("set", "reset"):
            out["shortcuts"] = desktop.install()
        _p(appicon.status() | out); return 0
    if a.cmd == "fonts":
        from . import fonts
        if a.action == "install":
            if not a.files:
                raise SystemExit("حدّدوا ملفّي الخط: rkpos fonts install adwa-assalaf.ttf adwa-assalaf_B.ttf")
            for f in a.files:
                fonts.install(Path(f).name, Path(f).read_bytes())
        if a.action in ("install", "system"):
            fonts.install_system()
        elif a.action == "remove":
            fonts.remove()
        _p(fonts.status() | {"system": fonts.system_status(), "system_folder": str(fonts.system_folder())}); return 0
    if a.cmd == "vault":
        from . import vault
        if a.vcmd == "add":
            r = vault.add(a.file, project=a.project, provenance=a.provenance, rights=a.rights, depositor=a.depositor)
            _p({"id": r["id"], "sha256": r["sha256"], "kind": r["kind"], "size": r["size"],
                "duplicate": bool(r.get("duplicate")), "vault_path": r["vault_path"]}); return 0
        if a.vcmd == "verify":
            r = vault.verify_all()
            _p(r); return 0 if not (r["missing"] or r["altered"]) else 2
        rows = [r for r in vault.load() if not a.project or r.get("project") == a.project]
        _p([{k: r.get(k) for k in ("id", "filename", "kind", "size", "project", "integrity", "last_verified")} for r in rows]
           or "الخزنة فارغة."); return 0
    if a.cmd == "backup":
        from . import vault
        _p(f"→ {vault.backup(Path(a.out) if a.out else None)}"); return 0
    if a.cmd == "skills-gen":
        from . import skillgen
        changed = skillgen.generate(check=a.check)
        if a.check and changed:
            _p("stale:\n" + "\n".join(map(str, changed))); return 1
        _p(f"{len(changed)} skill file(s) {'stale' if a.check else 'written'} ({len(skillgen.build())} available_now)"); return 0
    if a.cmd == "triangulate":
        from .verify import claims
        r = claims.triangulate_project(a.project)
        _p({"project": r["project"], "summary": r["summary"],
            "flagged": [{k: i[k] for k in ("claim_id", "status", "independent_origins", "type_labels", "best_tier", "flags_ar")}
                        for i in r["flagged"]]})
        return 0 if r["summary"]["passes"] else 2
    if a.cmd == "kpis":
        from . import dashboard
        if a.set_baseline:
            if not a.actor:
                _p("تثبيت خط الأساس قرار للمؤلف: أضيفوا --actor HUMAN-AUTHOR"); return 1
            _p(dashboard.set_baseline(a.actor, a.decision)); return 0
        k = dashboard.kpis()
        _p({**({"note": k["note"]} if k["note"] else {"baseline_at": k["baseline_at"]}),
            "items": [{x: i[x] for x in ("label", "value", "baseline", "delta")} for i in k["items"]]}); return 0
    if a.cmd == "memory-promote":
        from . import knowledge
        _p(knowledge.promote(a.memory_id, a.layer, a.approved_by)); return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
