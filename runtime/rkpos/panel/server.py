"""لوحة تحكم «مِداد» — خادم محلي على جهاز المؤلف (127.0.0.1 فقط).

- يفتح من أيقونة سطح المكتب (`rkpos panel`)، ويعرض كل إجراءات تفعيل الوكلاء.
- محمي برمز عشوائي يتولّد عند كل تشغيل ويُمرَّر في جزء الرابط (#) فلا يظهر في سجلات الخادم؛
  كل طلب API بلا الرمز يُرفض، وكل طلب بترويسة Host غير محلية يُرفض (حماية من DNS rebinding).
- لا يعرض أي مفتاح API؛ يكتفي بالإشارة إلى وجوده.
- القرارات L4 لا تُسجَّل إلا بإقرار صريح من المؤلف في الواجهة (confirm_author) وبصفة HUMAN-AUTHOR.
"""
from __future__ import annotations
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from .. import registry as R
from ..paths import ROOT, PROJECTS
from ..live import hidden as live_hidden

STATIC = Path(__file__).parent / "static"
STATE_FILE = Path(os.environ.get("RKPOS_PANEL_STATE", Path.home() / ".rkpos" / "panel.json"))
READABLE = ("projects", "workspace", "publishing/dashboard")
WRITE_LOCK = threading.Lock()
PROJECT_TYPES = ["intellectual_book", "academic_book", "policy_study", "systematic_review", "literature_review",
                 "foresight_study", "critical_edition", "journal_article", "op_ed", "strategic_report",
                 "translation", "re_edition", "novel", "novella", "short_story", "essay_collection"]
JOBS: dict[str, dict] = {}          # مهام الخلفية (الكتابة الكاملة) — في الذاكرة فقط
MIME = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}


class ApiError(Exception):
    pass


def _y(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def _need(d: dict, *keys):
    for k in keys:
        if d.get(k) in (None, ""):
            raise ApiError(f"الحقل «{k}» مطلوب")


def _author(d: dict):
    """إقرار المؤلف لكل قرار L4 من اللوحة."""
    if d.get("confirm_author") is not True:
        raise ApiError("قرار من مستوى L4: يلزم إقرار المؤلف (أقرّ بصفتي المؤلف)")


def _proj(pid: str) -> Path:
    p = (PROJECTS / pid).resolve()
    if not pid or not p.is_relative_to(PROJECTS.resolve()) or not (p / "manifest.yaml").exists():
        raise ApiError(f"مشروع غير موجود: {pid}")
    return p


# ------------------------------------------------------------------ قراءة
_AUTH_CACHE: dict = {}


def claude_logged_in(fresh: bool = False) -> bool | None:
    """هل Claude Code مسجّل الدخول؟ (تُخزَّن الإجابة 60 ثانية؛ None = تعذّر السؤال)."""
    import time
    from ..adapters.claude_code_adapter import auth_status
    if not fresh and _AUTH_CACHE and time.time() - _AUTH_CACHE["t"] < 60:
        return _AUTH_CACHE["v"]
    st = auth_status()
    v = None if st is None else bool(st.get("loggedIn"))
    _AUTH_CACHE.update(t=time.time(), v=v)
    return v


def engines(fresh: bool = False) -> dict:
    from ..adapters.claude_code_adapter import executable, login_command
    keys = {k: bool(os.environ.get(k)) for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "LOCAL_LLM_BASE_URL")}
    return {"claude_code": executable() is not None, "claude_code_path": executable(), "api_keys": keys,
            "claude_logged_in": claude_logged_in(fresh) if executable() else None,
            "claude_login_command": login_command(), "claude_in_path": bool(shutil.which("claude")),
            "platform": sys.platform,
            "default": os.environ.get("RKPOS_ENGINE", "auto"),
            "private_memory": (ROOT / "memory/author/private/items.jsonl").exists()}


def overview(_q) -> dict:
    from .. import dashboard
    projects = dashboard.collect()
    pending = [{"project": p["id"], "title": p["title"], "items": p["pending"], "next": p["next"]}
               for p in projects if p["pending"] or "AWAITING_AUTHOR" in str(p["stage"])]
    from .. import autopilot as AP
    return {"questions": AP.pending_questions(), "root": str(ROOT), "engines": engines(), "agents": len(R.agents()), "workflows": len(R.workflows()),
            "projects": projects, "pending": pending, "candidates": len(candidates(None)["items"])}


def agents(_q) -> dict:
    out = []
    for aid, a in R.agents().items():
        out.append({"id": aid, "name_ar": a["name_ar"], "name_en": a["name_en"], "type": a["type"],
                    "department": a["department"], "tier": a["model_tier"], "mvp": bool(a.get("mvp")),
                    "mission": " ".join(str(a.get("mission", "")).split()), "version": a.get("version"),
                    "reads_author": "MEM-AUTHOR" in a["memory"]["read"], "modes": a.get("modes", []),
                    "human_approval": a.get("human_approval", [])})
    return {"items": out, "departments": {k: v.get("name_ar", k) for k, v in R.departments().items()}}


def agent(q) -> dict:
    from ..runner import compose_system_prompt
    aid = q.get("id")
    a = R.agents().get(aid)
    if not a:
        raise ApiError(f"وكيل غير معروف: {aid}")
    return {"spec": a, "system_prompt": compose_system_prompt(aid, q.get("register") or None)}


def workflows(q) -> dict:
    from .. import workflow as WF
    if q.get("id"):
        w = R.workflows().get(q["id"])
        if not w:
            raise ApiError("سير عمل غير معروف")
        ctx = {"project_type": q.get("type") or (w.get("project_types") or [None])[0], "operating_model": q.get("model", "A")}
        try:
            steps = WF.expand(q["id"], ctx)
        except Exception as e:  # noqa: BLE001 — العرض لا يتوقف على شرط غير محسوم
            steps, ctx["note"] = w.get("steps", []), f"عرض خام: {e}"
        return {"workflow": w, "steps": steps, "context": ctx}
    return {"items": [{"id": k, "name_ar": w.get("name_ar"), "project_types": w.get("project_types", []),
                       "steps": len(w.get("steps", [])), "notes": w.get("notes")} for k, w in R.workflows().items()],
            "project_types": PROJECT_TYPES}


def project(q) -> dict:
    from .. import cost
    p = _proj(q.get("id"))
    runs = []
    if (p / "runs").exists():
        for d in sorted((p / "runs").iterdir()):
            if d.is_dir() and any(d.iterdir()):
                runs.append({"id": d.name, "files": sorted(f.name for f in d.iterdir() if f.is_file())})
    files = sorted(str(f.relative_to(ROOT)) for f in p.rglob("*") if f.is_file() and "runs" not in f.relative_to(p).parts)
    return {"manifest": _y(p / "manifest.yaml"), "state": _y(p / "state.yaml"), "plan": _y(p / "plan.yaml"),
            "decisions": (_y(p / "decisions.yaml") or {}).get("decisions", []), "runs": runs, "files": files,
            "cost": cost.report(p.name)}


def read_file(q) -> dict:
    rel = q.get("path", "")
    f = (ROOT / rel).resolve()
    if not any(f.is_relative_to((ROOT / r).resolve()) for r in READABLE) or not f.is_file():
        raise ApiError("مسار غير مسموح بقراءته من اللوحة")
    if f.suffix.lower() not in (".md", ".txt", ".yaml", ".yml", ".json", ".jsonl", ".html", ".bib", ".csv"):
        return {"path": rel, "binary": True, "size": f.stat().st_size}
    return {"path": rel, "text": f.read_text(encoding="utf-8", errors="replace")}


def candidates(_q) -> dict:
    from .. import knowledge as K
    cands = K._read(K.CANDIDATES) + K._read(K.PRIVATE_CANDIDATES)
    promoted = set()
    for f in K.LAYER_FILES.values():
        promoted |= {it["Memory_ID"] for it in K._read(f)}
    items = [c for c in cands if c["Memory_ID"] not in promoted]
    seen, uniq = set(), []
    for c in reversed(items):  # أحدث نسخة من كل مرشّح
        if c["Memory_ID"] not in seen:
            seen.add(c["Memory_ID"]); uniq.append(c)
    return {"items": sorted(uniq, key=lambda c: c["Memory_ID"])}


def memory(q) -> dict:
    from .. import knowledge as K
    out = {}
    for layer in K.LAYER_FILES:
        try:
            cur = K.current(layer)
        except FileNotFoundError:
            cur = {}
        out[layer] = {"count": len(cur), "items": list(cur.values()) if q.get("layer") == layer else []}
    return {"layers": out, "definitions": {k: v.get("name_ar", k) for k, v in R.memory().items()}}


def audit_log(q) -> dict:
    from .. import audit
    rows = audit.read(q.get("project") or None)
    n = int(q.get("limit", 80))
    return {"items": rows[-n:][::-1], "total": len(rows)}


def cost_report(q) -> dict:
    from .. import cost
    return cost.report(q.get("project") or None)


def governance(_q) -> dict:
    g = ROOT / "governance"
    return {"gates": R.load_yaml(g / "quality_gates.yaml")["gates"],
            "decision_rights": R.load_yaml(g / "decision_rights.yaml"),
            "council": R.load_yaml(g / "council.yaml")}


def genres_view(_q) -> dict:
    from .. import genres as GN
    return {"genres": GN.genres(), "levels": GN.levels(), "cross_genre": R.load_yaml(ROOT / "config/genres.yaml").get("cross_genre", {})}


def _running(pid: str) -> dict | None:
    return next((j for j in JOBS.values() if j["project"] == pid and j["state"] == "running"), None)


def labels_view(_q) -> dict:
    L = R.load_yaml(ROOT / "config/labels_ar.yaml")
    L["agents"] = {aid: a["name_ar"] for aid, a in R.agents().items()}
    return L


def autopilot_view(q) -> dict:
    from .. import autopilot as AP
    pid = _proj(q.get("id")).name
    ap = AP.load(pid)
    j = _running(pid)
    return {**ap, "mode": AP.mode_of(ap), "modes": {k: v["name_ar"] for k, v in AP.cfg()["modes"].items()},
            "running": bool(j and j.get("kind") == "autopilot"), "job": j}


def _start_autopilot(pid: str, engine: str, mode: str | None = None) -> dict:
    from .. import autopilot as AP
    if _running(pid):
        raise ApiError("يعمل لهذا المشروع تشغيل آخر الآن")
    jid = secrets.token_hex(6)
    job = {"id": jid, "project": pid, "kind": "autopilot", "state": "running", "error": None}
    JOBS[jid] = job

    def work():
        try:
            AP.run(pid, engine, mode=mode)
            job["state"] = "done"
        except Exception as e:  # noqa: BLE001
            job.update(state="error", error=f"{type(e).__name__}: {e}")
    threading.Thread(target=work, daemon=True).start()
    return job


def book_view(q) -> dict:
    from .. import book as B
    pid = _proj(q.get("id")).name
    try:
        ob = B.load(pid)
    except FileNotFoundError:
        return {"outline": None}
    return {"outline": ob, "voice": B.voice_report(pid), "estimate": B.estimate(pid) if ob["level"] == "full" else None,
            "job": (lambda j: j if j and j.get("kind") != "autopilot" else None)(_running(pid)), "book": str((PROJECTS / pid / "manuscript/book_full.md").relative_to(ROOT))
            if (PROJECTS / pid / "manuscript/book_full.md").exists() else None}


def book_unit(q) -> dict:
    pid = _proj(q.get("project")).name
    uid = q.get("unit", "")
    if not uid.isalnum():
        raise ApiError("وحدة غير صالحة")
    d = PROJECTS / pid / "manuscript/drafts"
    rd = lambda f: f.read_text(encoding="utf-8") if f.exists() else None  # noqa: E731
    return {"current": rd(d / f"{uid}.md"), "ai": rd(d / f"{uid}.ai.md"), "aligned": rd(d / f"{uid}.aligned.md"),
            "card": rd(d / f"{uid}.card.md"), "notes": rd(d / f"{uid}.notes.md"),
            "approved": rd(PROJECTS / pid / "manuscript/approved" / f"{uid}.md")}


def job_view(q) -> dict:
    j = JOBS.get(q.get("id", ""))
    if not j:
        raise ApiError("مهمة غير معروفة")
    return j


def live_view(q) -> dict:
    from .. import live
    pid = _proj(q.get("id")).name
    return live.read(pid, int(q.get("offset") or 0))


def docs_view(q) -> dict:
    """نصوص المشروع للشاشة الجانبية: الكتاب المجمّع، والوحدات، ومخرجات كل خطوة — بأسماء عربية."""
    from .. import autopilot as AP
    pid = _proj(q.get("id")).name
    root = PROJECTS / pid
    out = []
    full = root / "manuscript/book_full.md"
    if full.exists():
        out.append({"path": str(full.relative_to(ROOT)), "label": "العمل مجمّعاً", "group": "العمل"})
    try:
        from .. import book as B
        for u in B.load(pid)["units"]:
            for f, tag in ((root / "manuscript/approved" / f"{u['id']}.md", "معتمدة"), (root / "manuscript/drafts" / f"{u['id']}.md", "مسودة"),
                           (root / "manuscript/drafts" / f"{u['id']}.card.md", "بطاقة")):
                if f.exists():
                    out.append({"path": str(f.relative_to(ROOT)), "label": f"{u['id']} {u['title']} ({tag})", "group": "الوحدات"})
                    break
    except FileNotFoundError:
        pass
    for st in ST_plan(pid)["steps"]:
        f = root / "runs" / st["id"] / "output.md"
        if f.exists():
            out.append({"path": str(f.relative_to(ROOT)), "label": f"{st['id']} — {AP.task_ar(st['task'])}", "group": "مخرجات الخطوات"})
    for f in sorted((root / "manuscript/approved").glob("*.md")) if (root / "manuscript/approved").exists() else []:
        if not f.stem.startswith("U"):
            out.append({"path": str(f.relative_to(ROOT)), "label": f"المعتمد: {f.name}", "group": "العمل"})
    return {"items": out}


def ST_plan(pid):
    from .. import state as ST
    return ST.plan(pid)


GET = {"live": live_view, "docs": docs_view, "labels": labels_view, "autopilot": autopilot_view, "genres": genres_view, "book": book_view, "book_unit": book_unit, "job": job_view, "overview": overview, "agents": agents, "agent": agent, "workflows": workflows, "project": project,
       "file": read_file, "candidates": candidates, "memory": memory, "audit": audit_log, "cost": cost_report,
       "governance": governance, "engines": lambda q: engines(bool(q.get("fresh"))), "ping": lambda q: {"ok": True, "root": str(ROOT), "version": code_version(), "pid": os.getpid()}}


# ------------------------------------------------------------------ أفعال
def a_new_project(d):
    from .. import project as P
    _need(d, "title", "type")
    if d["type"] not in PROJECT_TYPES:
        raise ApiError("نوع مشروع غير معروف")
    m = P.new_project(d["title"], d["type"], domain=d.get("domain") or None, operating_model=d.get("model") or "A",
                      has_data=bool(d.get("has_data")), risk=d.get("risk") or "medium",
                      evidence_requirement=d.get("evidence") or "standard", publication_target=d.get("target") or None,
                      deadline=d.get("deadline") or None, genre=d.get("genre") or None,
                      production_level=d.get("level") or None,
                      target_pages=int(d["pages"]) if d.get("pages") else None,
                      words_per_page=int(d["wpp"]) if d.get("wpp") else None)
    out = {"project_id": m["project_id"], "workflow": m["workflow"], "agents": m["agents"], "autopilot": None}
    if d.get("autopilot") and (d.get("engine") or "manual") != "manual":
        out["autopilot"] = _start_autopilot(m["project_id"], d["engine"], d.get("mode") or None)
    return out


def _run_result(path: Path) -> dict:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    warn = path.parent / "warnings.txt"
    return {"path": str(path.relative_to(ROOT)), "kind": path.name, "text": text,
            "warnings": [w for w in warn.read_text(encoding="utf-8").splitlines() if w] if warn.exists() else []}


def a_run_step(d):
    from .. import runner
    _need(d, "project")
    _proj(d["project"])
    engine = d.get("engine") or "manual"
    path = runner.run_step(d["project"], d.get("step") or None, live=engine != "manual",
                           engine=None if engine == "manual" else engine)
    return _run_result(path)


def a_record_output(d):
    from .. import runner
    import tempfile
    _need(d, "project", "step", "text")
    _proj(d["project"])
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(d["text"])
    try:
        dst = runner.record_output(d["project"], d["step"], Path(f.name))
    finally:
        os.unlink(f.name)
    return {"path": str(dst.relative_to(ROOT))}


def a_complete(d):
    from .. import runner, state as ST
    import tempfile
    _need(d, "project", "step", "actor")
    _proj(d["project"])
    step = next((s for s in ST.plan(d["project"])["steps"] if s["id"] == d["step"]), None)
    if step is None:
        raise ApiError("خطوة غير موجودة")
    if d["actor"] == "HUMAN-AUTHOR" or step.get("decision_level") == "L4" or d.get("approved_text"):
        _author(d)
    approved = None
    if d.get("approved_text"):
        name = Path(d.get("approved_name") or f"{d['step']}_approved.md").name
        tmp = Path(tempfile.mkdtemp(prefix="rkpos-ap-"))
        approved = tmp / name
        approved.write_text(d["approved_text"], encoding="utf-8")
    try:
        return {"decision": runner.complete(d["project"], d["step"], d["actor"], d.get("decision") or None, approved)}
    except PermissionError as e:
        raise ApiError(f"مرفوض بالحوكمة: {e}") from e
    finally:
        if approved:
            shutil.rmtree(approved.parent, ignore_errors=True)


def a_adhoc(d):
    from .. import runner
    _need(d, "agent", "task")
    engine = d.get("engine") or "manual"
    return runner.run_adhoc(d["agent"], d["task"], register=d.get("register") or None, project=d.get("project") or None,
                            context=d.get("context") or "", engine=engine, genre=d.get("genre") or None)


def a_check_text(d):
    from ..verify import citations, claims, sources, terms
    from .. import stylometry as S
    _need(d, "text")
    text, pid = d["text"], d.get("project") or None
    srcs = sources.load()
    if pid:
        srcs = sources.load(_proj(pid) / "research/sources.jsonl") + srcs
    rep = {"claims": claims.audit(text), "citations": citations.audit(text, srcs), "terminology": terms.check(text)}
    reg = d.get("register") or (S.register_for(pid) if pid else None)
    from ..genres import VOICE_REGISTERS, discipline_report
    ref = S.load_reference(reg) if reg in VOICE_REGISTERS else None
    if reg and reg not in VOICE_REGISTERS:
        rep["discipline"] = discipline_report(text)
    prof = S.profile(text)
    prof.pop("top_bigrams", None)
    rep["style_profile"] = prof
    if ref:
        rep["style_deviation"] = S.distance(prof, ref)
        assisted = S.load_assisted_pole()
        if assisted and reg in S.POLE_REGISTERS:
            rep["voice_pole"] = S.pole(prof, ref, assisted)
    rep["register"] = reg
    return rep


def a_verify_doi(d):
    from ..verify import doi
    _need(d, "doi")
    return doi.verify(d["doi"], d.get("title") or None, int(d["year"]) if d.get("year") else None)


def a_select(d):
    from .. import selection
    _need(d, "type")
    return selection.select({"project_type": d["type"], "operating_model": d.get("model") or "A", "domain": d.get("domain") or None,
                             "has_data": bool(d.get("has_data")), "risk": d.get("risk") or "medium",
                             "evidence_requirement": d.get("evidence") or "standard", "publication_target": d.get("target") or None})


def a_validate(_d):
    from .. import generate
    errs = R.check_integrity() + [f"stale generated file: {p}" for p in generate.write(check=True)]
    return {"ok": not errs, "errors": errs}


def a_generate(_d):
    from .. import generate
    return {"written": [str(p) for p in generate.write()]}


def a_eval(d):
    from .. import evals
    ids = [d["agent"]] if d.get("agent") else list(R.agents())
    if d.get("live"):
        if not d.get("agent"):
            raise ApiError("التقييم الحي لوكيل واحد في كل مرة (يستهلك رصيداً)")
        return evals.live_run(d["agent"], engine=d.get("engine") or None)
    errs = [e for i in ids for e in evals.offline_check(i)]
    return {"ok": not errs, "errors": errs, "suites": len(ids)}


def a_dashboard(_d):
    from .. import dashboard
    return {"path": str(Path(dashboard.build()).relative_to(ROOT))}


def a_security_scan(_d):
    r = subprocess.run([sys.executable, str(ROOT / "scripts/security_scan.py")], cwd=ROOT, capture_output=True, text=True, **live_hidden())
    return {"ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()}


def a_promote(d):
    from .. import knowledge
    _need(d, "memory_id", "layer")
    if d["layer"] in ("MEM-INSTITUTIONAL", "MEM-AUTHOR"):
        _author(d)
    try:
        return knowledge.promote(d["memory_id"], d["layer"], "HUMAN-AUTHOR" if d.get("confirm_author") else "AG-KNW")
    except (PermissionError, KeyError) as e:
        raise ApiError(str(e)) from e


def a_amend(d):
    from .. import knowledge
    _need(d, "memory_id", "layer", "content", "reason")
    _author(d)
    return knowledge.amend(d["memory_id"], d["layer"], d["content"], "HUMAN-AUTHOR", d["reason"])


def a_open_folder(d):
    rel = d.get("path") or ""
    f = (ROOT / rel).resolve()
    if not f.is_relative_to(ROOT.resolve()) or not f.exists():
        raise ApiError("مسار غير موجود")
    target = str(f if f.is_dir() else f.parent)
    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", target])
    return {"opened": target}


def _book_guard(d):
    _need(d, "project")
    pid = _proj(d["project"]).name
    if _running(pid):
        raise ApiError("الكتابة الكاملة جارية لهذا المشروع؛ انتظروا انتهاءها")
    return pid


def _eng(d):
    return d.get("engine") or "manual"


def b_skeleton(d):
    from .. import book as B
    return B.skeleton(_book_guard(d), int(d.get("n") or 5))


def b_set_units(d):
    from .. import book as B
    pid = _book_guard(d)
    return B.set_units(pid, d.get("units") or [], force=bool(d.get("force") and d.get("confirm_author")))


def b_propose(d):
    from .. import book as B
    return B.propose_outline(_book_guard(d), _eng(d), int(d["n"]) if d.get("n") else None, d.get("guidance") or "")


def b_import_outline(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "text")
    return B.set_units(pid, B.parse_outline(d["text"]))


def b_approve_outline(d):
    from .. import book as B
    pid = _book_guard(d)
    _author(d)
    return B.approve_outline(pid, "HUMAN-AUTHOR")


def b_draft(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit")
    try:
        return B.draft_unit(pid, d["unit"], _eng(d))
    except PermissionError as e:
        raise ApiError(str(e)) from e


def b_record(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit", "text")
    text = B.extract(d["text"])[0] if B.BEGIN in d["text"] else d["text"]
    return B.record_unit(pid, d["unit"], text, source="ai" if d.get("source") != "author" else "author")


def b_revise(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit", "text")
    return B.revise_unit(pid, d["unit"], d["text"])


def b_align(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit")
    return B.align_voice(pid, d["unit"], _eng(d))


def b_adopt_aligned(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit")
    f = PROJECTS / pid / "manuscript/drafts" / f"{d['unit']}.aligned.md"
    if not f.exists():
        raise ApiError("لا نسخة مواءمة لهذه الوحدة")
    return B.revise_unit(pid, d["unit"], f.read_text(encoding="utf-8"))


def b_approve_unit(d):
    from .. import book as B
    pid = _book_guard(d)
    _need(d, "unit")
    _author(d)
    return B.approve_unit(pid, d["unit"], "HUMAN-AUTHOR", d.get("text") or None)


def b_assemble(d):
    from .. import book as B
    return B.assemble(_book_guard(d))


def b_draft_all(d):
    """تشغيل في الخلفية مع تقدّم قابل للمتابعة؛ يتطلب إقرار التقدير والكلفة."""
    from .. import book as B
    pid = _book_guard(d)
    if _eng(d) == "manual":
        raise ApiError("الكتابة الكاملة تحتاج محرّكاً آلياً: اختاروا Claude Code أو API")
    if d.get("confirm_cost") is not True:
        raise ApiError("أقرّوا تقدير الحجم والكلفة أولاً")
    ob = B.load(pid)
    if ob["level"] != "full":
        raise ApiError("الكتابة الكاملة لمستوى «الكامل» وحده")
    if not ob["outline_approved"]:
        raise ApiError("اعتمدوا المخطط أولاً (L4)")
    jid = secrets.token_hex(6)
    job = {"id": jid, "project": pid, "state": "running", "done": 0, "total": 0, "current": None, "error": None, "result": None}
    JOBS[jid] = job

    def prog(i, n, uid):
        job.update(done=i, total=n, current=uid)

    def work():
        try:
            job["result"] = B.draft_all(pid, _eng(d), prog)
            job["state"] = "done"
        except Exception as e:  # noqa: BLE001 — يُعرض في اللوحة؛ الوحدات المكتوبة قبل الخطأ محفوظة
            job.update(state="error", error=f"{type(e).__name__}: {e}")
    threading.Thread(target=work, daemon=True).start()
    return job


def a_claude_login(_d):
    from ..adapters.claude_code_adapter import open_login_window, AdapterUnavailable
    try:
        open_login_window()
    except AdapterUnavailable as e:
        raise ApiError(str(e)) from e
    _AUTH_CACHE.clear()
    return {"opened": True}


def a_autopilot_start(d):
    _need(d, "project")
    pid = _proj(d["project"]).name
    eng = d.get("engine") or "manual"
    if eng == "manual":
        raise ApiError("التشغيل الآلي يحتاج محرّكاً آلياً: اختاروا Claude Code أعلى الصفحة")
    return _start_autopilot(pid, eng, d.get("mode") or None)


def a_autopilot_answer(d):
    from .. import autopilot as AP
    _need(d, "project", "qid", "choice")
    pid = _proj(d["project"]).name
    if _running(pid):
        raise ApiError("ينتظر انتهاء الخطوة الجارية")
    ap = AP.answer(pid, d["qid"], d["choice"], d.get("note") or "")
    if ap["status"] != "paused":
        _start_autopilot(pid, ap.get("engine") or d.get("engine") or "claude_code")
    return {"status": ap["status"]}


def a_stop_now(d):
    """إيقاف طارئ: يقطع كتابة الوكيل فوراً، ويوقف الطيار بسؤال لتوجيه المسار."""
    from .. import autopilot as AP, live
    _need(d, "project")
    pid = _proj(d["project"]).name
    AP.request_stop(pid)
    return {"killed": live.stop_now(pid)}


def a_autopilot_note(d):
    from .. import autopilot as AP
    _need(d, "project", "note")
    return {"guidance": AP.add_note(_proj(d["project"]).name, d["note"]).get("guidance", {}).get("*")}


def a_autopilot_stop(d):
    from .. import autopilot as AP
    _need(d, "project")
    return AP.request_stop(_proj(d["project"]).name)


def a_claude_add_path(_d):
    from ..adapters.claude_code_adapter import add_to_user_path, AdapterUnavailable
    try:
        return {"added": add_to_user_path()}
    except AdapterUnavailable as e:
        raise ApiError(str(e)) from e


POST = {"stop_now": a_stop_now, "autopilot_note": a_autopilot_note, "autopilot_start": a_autopilot_start, "autopilot_answer": a_autopilot_answer, "autopilot_stop": a_autopilot_stop,
        "claude_add_path": a_claude_add_path, "claude_login": a_claude_login, "book_skeleton": b_skeleton, "book_set_units": b_set_units, "book_propose": b_propose,
        "book_import_outline": b_import_outline, "book_approve_outline": b_approve_outline, "book_draft": b_draft,
        "book_record": b_record, "book_revise": b_revise, "book_align": b_align, "book_adopt_aligned": b_adopt_aligned,
        "book_approve_unit": b_approve_unit, "book_assemble": b_assemble, "book_draft_all": b_draft_all,
        "new_project": a_new_project, "run_step": a_run_step, "record_output": a_record_output, "complete": a_complete,
        "adhoc": a_adhoc, "check_text": a_check_text, "verify_doi": a_verify_doi, "select": a_select,
        "validate": a_validate, "generate": a_generate, "eval": a_eval, "dashboard": a_dashboard,
        "security_scan": a_security_scan, "promote": a_promote, "amend": a_amend, "open_folder": a_open_folder}
READ_ONLY_POST = {"stop_now", "autopilot_note", "check_text", "verify_doi", "select", "validate", "security_scan", "open_folder"}


# ------------------------------------------------------------------ HTTP
def make_handler(token: str, port_ref: dict):
    class H(BaseHTTPRequestHandler):
        server_version = "MIDAD-Panel/1.0"

        def log_message(self, fmt, *args):  # لا تُطبع الطلبات (قد تحمل نصوصاً خاصة)
            pass

        def _host_ok(self) -> bool:
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ("127.0.0.1", "localhost")

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                             "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))

        def _auth(self) -> bool:
            if not self._host_ok():
                self._json(403, {"ok": False, "error": "host"}); return False
            if not secrets.compare_digest(self.headers.get("X-Rkpos-Token", ""), token):
                self._json(401, {"ok": False, "error": "token"}); return False
            return True

        def do_GET(self):
            u = urlparse(self.path)
            if not u.path.startswith("/api/"):
                if not self._host_ok():
                    return self._json(403, {"ok": False, "error": "host"})
                name = "index.html" if u.path in ("/", "/index.html") else u.path.lstrip("/")
                f = (STATIC / name).resolve()
                if not f.is_relative_to(STATIC.resolve()) or not f.is_file():
                    return self._send(404, b"not found", "text/plain")
                return self._send(200, f.read_bytes(), MIME.get(f.suffix, "application/octet-stream"))
            if not self._auth():
                return
            if u.path == "/api/export":
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                f = (ROOT / q.get("path", "")).resolve()
                if not any(f.is_relative_to((ROOT / r).resolve()) for r in READABLE) or not f.is_file():
                    return self._json(400, {"ok": False, "error": "مسار غير مسموح"})
                from ..export import to_docx
                return self._send(200, to_docx(f.read_text(encoding="utf-8"), q.get("title") or None,
                                               clean=q.get("clean", "1") == "1"),
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if u.path == "/api/raw":
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                f = (ROOT / q.get("path", "")).resolve()
                if not any(f.is_relative_to((ROOT / r).resolve()) for r in READABLE) or not f.is_file():
                    return self._json(400, {"ok": False, "error": "مسار غير مسموح"})
                return self._send(200, f.read_bytes(), "application/octet-stream")
            fn = GET.get(u.path[5:])
            if not fn:
                return self._json(404, {"ok": False, "error": "unknown endpoint"})
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            self._call(fn, q)

        def do_POST(self):
            if not self._auth():
                return
            name = urlparse(self.path).path[5:]
            if name == "shutdown":
                self._json(200, {"ok": True, "data": {"stopping": True}})
                threading.Thread(target=port_ref["httpd"].shutdown, daemon=True).start()
                return
            fn = POST.get(name)
            if not fn:
                return self._json(404, {"ok": False, "error": "unknown action"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                d = json.loads(self.rfile.read(n).decode("utf-8") or "{}") if n else {}
            except (ValueError, json.JSONDecodeError):
                return self._json(400, {"ok": False, "error": "bad json"})
            if name in READ_ONLY_POST:
                return self._call(fn, d)
            with WRITE_LOCK:
                self._call(fn, d)

        def _call(self, fn, arg):
            try:
                self._json(200, {"ok": True, "data": fn(arg)})
            except ApiError as e:
                self._json(400, {"ok": False, "error": str(e)})
            except (KeyError, ValueError, PermissionError, FileNotFoundError) as e:
                self._json(400, {"ok": False, "error": f"{type(e).__name__}: {e}"})
            except Exception as e:  # noqa: BLE001
                self._json(500, {"ok": False, "error": f"{type(e).__name__}: {e}"})
    return H


def code_version() -> str:
    """بصمة نسخة الشيفرة الجارية: تتغير مع كل تحديث للمنظومة."""
    import hashlib
    pkg = Path(__file__).resolve().parents[1]
    h = hashlib.sha1()
    for f in sorted(pkg.rglob("*")):
        if f.suffix in (".py", ".js", ".html", ".css") and "__pycache__" not in f.parts:
            h.update(f.name.encode())
            h.update(str(f.stat().st_mtime_ns).encode())
    return h.hexdigest()[:12]


def _existing() -> dict | None:
    """لوحة تعمل مسبقاً لهذا المستودع؟ إن كانت من النسخة نفسها تُفتح نافذتها؛
    وإن كانت أقدم (بقيت تعمل في الخلفية بعد التحديث) تُوقَف ليعمل الإصدار الجديد."""
    import time
    import urllib.request
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if st.get("root") != str(ROOT):
            return None
        hdr = {"X-Rkpos-Token": st["token"]}
        req = urllib.request.Request(f"http://127.0.0.1:{st['port']}/api/ping", headers=hdr)
        with urllib.request.urlopen(req, timeout=1.5) as r:
            if r.status != 200:
                return None
        if st.get("version") == code_version():
            return st
        stop = urllib.request.Request(f"http://127.0.0.1:{st['port']}/api/shutdown", data=b"{}", method="POST",
                                      headers={**hdr, "Content-Type": "application/json"})
        urllib.request.urlopen(stop, timeout=3).read()
        time.sleep(1.5)
        _say("أُوقفت نسخة قديمة من اللوحة كانت تعمل في الخلفية.")
    except Exception:  # noqa: BLE001
        pass
    return None


def _say(msg: str) -> None:
    if sys.stdout is not None:  # pythonw (أيقونة ويندوز) بلا طرفية
        try:
            print(msg, flush=True)
        except (OSError, UnicodeEncodeError):
            pass


def serve(port: int = 0, open_browser: bool = True, reuse: bool = True) -> None:
    if reuse and (st := _existing()):
        url = f"http://127.0.0.1:{st['port']}/#t={st['token']}"
        _say(f"اللوحة تعمل مسبقاً: {url}")
        if open_browser:
            webbrowser.open(url)
        return
    token = secrets.token_urlsafe(24)
    port_ref: dict = {}
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(token, port_ref))
    port = httpd.server_address[1]
    port_ref["httpd"] = httpd
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"port": port, "token": token, "root": str(ROOT), "pid": os.getpid(),
                                      "version": code_version()}), encoding="utf-8")
    try:
        os.chmod(STATE_FILE, 0o600)
    except OSError:
        pass
    url = f"http://127.0.0.1:{port}/#t={token}"
    _say(f"لوحة «مِداد» تعمل على {url}\nأوقفها من الإعدادات في اللوحة أو بـ Ctrl+C.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        try:
            STATE_FILE.unlink()
        except OSError:
            pass
