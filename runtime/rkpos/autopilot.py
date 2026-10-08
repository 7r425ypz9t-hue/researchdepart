"""الطيار الآلي: يمضي بخطة المشروع وكيلاً بعد وكيل، ولا يتوقف إلا عند قرار يملكه المؤلف.

- الخطوات L1/L2/L3: تُنفَّذ بالمحرّك المختار وتُغلق آلياً باسم الوكيل أو المشرف أو المجلس (حقوق القرار).
- الخطوات L4 وما أُسند إلى المؤلف: يتوقف الطيار ويطرح سؤالاً بخيارات سريعة معدّة سلفاً (config/autopilot.yaml).
- مهام المخطط والكتابة: يتولاها محرّك بناء العمل (book.py) بحسب مستوى الإنتاج.
- تمرّر لكل خطوة نصوص المخرجات السابقة والمسودة المجمّعة، فيعمل المدقق والمحرر على المحتوى نفسه.
الأسئلة تُشتق من حالة المشروع: الإيقاف ثم الاستئناف يعيد طرح السؤال القائم، فلا يضيع قرار.
"""
from __future__ import annotations
import secrets

import yaml

from . import audit, book as B, cost as C, genres as GN, registry as R, runner, state as ST
from .ids import now_iso
from .paths import CONFIG, PROJECTS

MAX_MATERIAL_CHARS = 60000


def cfg() -> dict:
    return R.load_yaml(CONFIG / "autopilot.yaml")


def labels() -> dict:
    return R.load_yaml(CONFIG / "labels_ar.yaml")


def task_ar(task: str) -> str:
    return labels()["tasks"].get(task, task)


# ------------------------------------------------------------------ الحالة
def _path(pid):
    return PROJECTS / pid / "autopilot.yaml"


def load(pid: str) -> dict:
    p = _path(pid)
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    return {"project_id": pid, "status": "idle", "engine": None, "question": None, "log": [],
            "budget_override": False, "guidance": {}}


def save(pid: str, ap: dict) -> None:
    ap["updated"] = now_iso()
    ap["log"] = ap["log"][-200:]
    _path(pid).write_text(yaml.safe_dump(ap, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _log(pid: str, ap: dict, msg: str) -> None:
    ap["log"].append({"t": now_iso(), "msg": msg})
    save(pid, ap)


def _ask(pid: str, ap: dict, kind: str, step: dict | None = None, unit: dict | None = None,
         body: str = "", file: str | None = None) -> str:
    spec = cfg()["questions"][kind]
    fmt = {"task": task_ar(step["task"]) if step else "", "unit": f"{unit['id']} {unit['title']}" if unit else ""}
    ap["question"] = {"id": secrets.token_hex(4), "kind": kind, "title": spec["title"].format(**fmt),
                      "prompt": spec["prompt"], "body": body, "file": file,
                      "step": step["id"] if step else None, "unit": unit["id"] if unit else None,
                      "choices": [{k: c[k] for k in ("id", "label") if k in c} | {"needs_note": bool(c.get("needs_note")),
                                  "style": c.get("style", "")} for c in spec["choices"]], "asked": now_iso()}
    ap["status"] = "waiting"
    _log(pid, ap, f"سؤال للمؤلف: {ap['question']['title']}")
    return "wait"


# ------------------------------------------------------------------ المواد الممرَّرة
def _out(pid, step_id):
    f = PROJECTS / pid / "runs" / step_id / "output.md"
    return f if f.exists() else None


def materials(pid: str, step: dict | None = None, ap: dict | None = None) -> str:
    parts = []
    if ap and step and ap.get("guidance", {}).get(step["id"]):
        parts.append(f"## توجيه المؤلف لهذه الخطوة\n{ap['guidance'][step['id']]}")
    bible = PROJECTS / pid / "story_bible.md"
    if bible.exists():
        parts.append("## كرّاسة الرواية\n" + bible.read_text(encoding="utf-8")[:12000])
    done = [s for s in ST.plan(pid)["steps"] if s["status"] == "DONE" and _out(pid, s["id"])]
    for s in done[-3:]:
        parts.append(f"## مخرج {s['id']} — {task_ar(s['task'])}\n" + _out(pid, s["id"]).read_text(encoding="utf-8")[:8000])
    full = PROJECTS / pid / "manuscript/book_full.md"
    if full.exists():
        parts.append("## المسودة المجمّعة للعمل\n" + full.read_text(encoding="utf-8")[:MAX_MATERIAL_CHARS])
    return "\n\n".join(parts)


# ------------------------------------------------------------------ التشغيل
def _agent(step):
    return step.get("assigned_agent", step.get("agent"))


def _is_author_step(step) -> bool:
    a = _agent(step)
    return a == "HUMAN-AUTHOR" or (a == "AG-ORC" and step.get("human_approval") and step["task"].startswith("request_"))


def _auto_actor(step) -> str:
    lvl = step.get("decision_level")
    if lvl == "L3":
        return "AG-COUNCIL"
    if lvl == "L2":
        return step.get("reviewer") if step.get("reviewer") not in (None, "AG-COUNCIL") else "AG-ORC"
    return _agent(step) if _agent(step) not in ("HUMAN-AUTHOR", None) else "AG-ORC"


def _run_agent_step(pid, ap, step, engine) -> bool:
    """يشغّل الوكيل؛ يعيد True إن أنتج مخرجاً."""
    _log(pid, ap, f"{step['id']} — {task_ar(step['task'])} ← {_agent(step)}")
    runner.run_step(pid, step["id"], live=True, engine=engine, extra_context=materials(pid, step, ap))
    return _out(pid, step["id"]) is not None


def _outline(pid, ap, step, engine, completes_step: bool) -> str | None:
    ob = B.load(pid)
    if not ob["units"]:
        if GN.genres()[ob["genre"]].get("max_words"):
            B.skeleton(pid, 1)
            B.approve_trivial_outline(pid)
            return None
        _log(pid, ap, "يقترح الوكيل مخطط العمل")
        B.propose_outline(pid, engine, guidance=ap.get("guidance", {}).get(step["id"], ""))
        ob = B.load(pid)
    if not ob["outline_approved"]:
        body = "\n".join(f"{u['id']} — {u['title']} ({u['target_words'] or '—'} كلمة): {u['brief']}" for u in ob["units"])
        return _ask(pid, ap, "outline_approval", step, body=body)
    if completes_step:
        runner.complete(pid, step["id"], "HUMAN-AUTHOR", "اعتماد المخطط (معتمد في محرّك البناء)")
    return None


def _drafting(pid, ap, step, engine) -> str | None:
    r = _outline(pid, ap, step, engine, completes_step=False)
    if r:
        return r
    ob = B.load(pid)
    level = ob["level"]
    pending = [u for u in ob["units"] if u["status"] != "APPROVED"]
    if not pending:
        B.assemble(pid)
        runner.complete(pid, step["id"], _auto_actor(step))
        _log(pid, ap, "اعتُمدت الوحدات كلها وجُمّع العمل")
        return None
    if level == "scaffold":
        for u in [u for u in ob["units"] if u["status"] == "PLANNED"]:
            _log(pid, ap, f"بطاقة {u['id']} — {u['title']}")
            B.draft_unit(pid, u["id"], engine)
        u = next(u for u in B.load(pid)["units"] if u["status"] != "APPROVED")
        return _ask(pid, ap, "scaffold_write", step, unit=u, file=f"projects/{pid}/manuscript/drafts/{u['id']}.card.md")
    if level == "staged":
        u = pending[0]
        if u["status"] in ("PLANNED", "CARDED"):
            _log(pid, ap, f"يكتب الوكيل {u['id']} — {u['title']}")
            B.draft_unit(pid, u["id"], engine)
            u = next(x for x in B.load(pid)["units"] if x["id"] == u["id"])
        return _ask(pid, ap, "unit_approval", step, unit=u, body=_voice_line(u),
                    file=f"projects/{pid}/manuscript/drafts/{u['id']}.md")
    # full
    if any(u["status"] in ("PLANNED", "CARDED") for u in ob["units"]):
        _log(pid, ap, f"تُكتب الوحدات كلها ({len(ob['units'])})")
        B.draft_all(pid, engine, lambda i, n, uid: uid and _log(pid, ap, f"[{i + 1}/{n}] {uid}"))
    rep = B.voice_report(pid)
    body = (f"{rep['total_words']} كلمة من {rep.get('target_words') or '—'}؛ "
            + (f"وحدات أقرب إلى الصياغة المُعانة: {'، '.join(rep['flagged'])}" if rep["flagged"] else "لا وحدات معلَّمة"))
    return _ask(pid, ap, "book_review", step, body=body, file=f"projects/{pid}/manuscript/book_full.md")


def _voice_line(u):
    v = (u.get("voice") or {}).get("pole") or {}
    return f"{u.get('words', 0)} كلمة من {u.get('target_words') or '—'}" + (f"؛ القرب من الصياغة المُعانة {v['assisted_share']}" if v else "")


def _step(pid, ap, step, engine) -> str | None:
    c = cfg()
    task = step["task"]
    if task in c["outline_tasks"]:
        return _outline(pid, ap, step, engine, completes_step=True)
    if task in c["draft_tasks"]:
        return _drafting(pid, ap, step, engine)
    out = _out(pid, step["id"])
    if _is_author_step(step):
        last = [s for s in ST.plan(pid)["steps"] if s["status"] == "DONE" and _out(pid, s["id"])]
        full = PROJECTS / pid / "manuscript/book_full.md"
        f = f"projects/{pid}/manuscript/book_full.md" if full.exists() else (
            f"projects/{pid}/runs/{last[-1]['id']}/output.md" if last else None)
        return _ask(pid, ap, "step_approval", step, file=f)
    if not out or step["status"] in ("PENDING", "CONDITIONAL", "REJECTED"):
        if not _run_agent_step(pid, ap, step, engine):
            raise RuntimeError("لم يُنتج المحرّك مخرجاً (تحققوا من تسجيل الدخول إلى Claude أو من المفتاح)")
    if step.get("human_approval") or step.get("decision_level") == "L4":
        return _ask(pid, ap, "step_approval", step, file=f"projects/{pid}/runs/{step['id']}/output.md")
    runner.complete(pid, step["id"], _auto_actor(step))
    return None


def run(pid: str, engine: str, max_steps: int = 400) -> dict:
    if engine in (None, "manual"):
        raise ValueError("الطيار الآلي يحتاج محرّكاً آلياً (Claude Code أو API)")
    ap = load(pid)
    if ap.get("question"):
        return ap
    ap.update(status="running", engine=engine, stop_requested=False)
    _log(pid, ap, "بدأ الطيار الآلي")
    for _ in range(max_steps):
        if load(pid).get("stop_requested"):
            ap = load(pid)
            ap.update(status="paused", stop_requested=False)
            _log(pid, ap, "أُوقف الطيار الآلي بطلب المؤلف")
            break
        plan = ST.plan(pid)
        step = ST.next_step(plan)
        if step is None:
            ap["status"] = "done"
            _log(pid, ap, "اكتملت خطة المشروع")
            break
        budget = GN.manifest(pid).get("budget_usd")
        if budget and not ap.get("budget_override") and C.report(pid)["total_usd"] >= budget:
            _ask(pid, ap, "budget", step)
            break
        try:
            if _step(pid, ap, step, engine) == "wait":
                break
        except Exception as e:  # noqa: BLE001 — يُعرض سؤالاً للمؤلف؛ لا يُبتلع
            ap = load(pid)
            _ask(pid, ap, "error", step, body=f"{type(e).__name__}: {e}")
            break
        ap = load(pid)
    save(pid, ap)
    return ap


# ------------------------------------------------------------------ الإجابة
def answer(pid: str, qid: str, choice_id: str, note: str = "") -> dict:
    ap = load(pid)
    q = ap.get("question")
    if not q or q["id"] != qid:
        raise ValueError("السؤال لم يعد قائماً؛ حدّثوا الصفحة")
    spec = {c["id"]: c for c in cfg()["questions"][q["kind"]]["choices"]}
    if choice_id not in spec:
        raise ValueError("خيار غير معروف")
    c = spec[choice_id]
    if c.get("needs_note") and not note.strip():
        raise ValueError("هذا الخيار يحتاج ملاحظة أو توجيهاً منكم")
    act, engine = c["action"], ap.get("engine") or "claude_code"
    decision = c["label"] + (f" — {note.strip()}" if note.strip() else "")
    step = next((s for s in ST.plan(pid)["steps"] if s["id"] == q["step"]), None) if q.get("step") else None
    uid = q.get("unit")
    if act == "approve_step":
        runner.complete(pid, step["id"], "HUMAN-AUTHOR", f"{task_ar(step['task'])}: {decision}")
    elif act == "redo_step":
        ap.setdefault("guidance", {})[step["id"]] = note.strip()
        out = _out(pid, step["id"])
        if out:
            out.rename(out.with_name("output.prev.md"))
        plan = ST.plan(pid)
        next(s for s in plan["steps"] if s["id"] == step["id"])["status"] = "PENDING"
        ST.save_plan(pid, plan)
    elif act == "approve_outline":
        B.approve_outline(pid, "HUMAN-AUTHOR")
        if step and step["task"] in cfg()["outline_tasks"]:
            runner.complete(pid, step["id"], "HUMAN-AUTHOR", f"اعتماد المخطط: {decision}")
    elif act == "repropose_outline":
        B.propose_outline(pid, engine, guidance=note.strip())
    elif act == "approve_unit":
        B.approve_unit(pid, uid, "HUMAN-AUTHOR")
    elif act == "align_then_approve":
        r = B.align_voice(pid, uid, engine)
        B.revise_unit(pid, uid, r["text"])
        B.approve_unit(pid, uid, "HUMAN-AUTHOR")
    elif act == "redraft_unit":
        ap.setdefault("guidance", {})[step["id"] if step else uid] = note.strip()
        _redraft(pid, uid, engine, note.strip())
    elif act == "align_flagged":
        for f in B.voice_report(pid)["flagged"]:
            r = B.align_voice(pid, f, engine)
            B.revise_unit(pid, f, r["text"])
    elif act == "approve_all_units":
        for u in B.load(pid)["units"]:
            if u["status"] != "APPROVED":
                B.approve_unit(pid, u["id"], "HUMAN-AUTHOR")
    elif act == "continue_budget":
        ap["budget_override"] = True
    elif act == "skip_step":
        runner.complete(pid, step["id"], "HUMAN-AUTHOR", f"تخطّي «{task_ar(step['task'])}» بقرار المؤلف" + (f" — {note}" if note else ""))
    elif act in ("pause", "retry"):
        pass
    ap["question"] = None
    ap["status"] = "paused" if act == "pause" else "ready"
    ap["log"].append({"t": now_iso(), "msg": f"قرار المؤلف: {q['title']} ← {decision}"})
    save(pid, ap)
    audit.log("HUMAN-AUTHOR", f"autopilot_answer:{q['kind']}", project=pid, decision=decision,
              decision_level="L4" if act not in ("pause", "retry") else None, approval="HUMAN-AUTHOR")
    return ap


def _redraft(pid, uid, engine, note):
    """إعادة كتابة وحدة بتوجيه المؤلف: يُلحق التوجيه بموجزها ثم تُكتب من جديد."""
    ob = B.load(pid)
    for u in ob["units"]:
        if u["id"] == uid and note:
            u["brief"] = (u["brief"] + " | توجيه المؤلف: " + note).strip(" |")
    B.save(pid, ob)
    B.draft_unit(pid, uid, engine)


def pending_questions() -> list[dict]:
    out = []
    for p in sorted(PROJECTS.glob("RKP-*")):
        f = p / "autopilot.yaml"
        if f.exists():
            ap = yaml.safe_load(f.read_text(encoding="utf-8"))
            if ap.get("question"):
                out.append({"project": p.name, **ap["question"]})
    return out


def request_stop(pid: str) -> dict:
    """يتوقف الطيار بعد إتمام الخطوة الجارية (لا تُقطع خطوة في منتصفها)."""
    ap = load(pid)
    ap["stop_requested"] = True
    save(pid, ap)
    return ap
