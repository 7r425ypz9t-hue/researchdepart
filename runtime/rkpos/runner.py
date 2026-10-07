"""تنفيذ خطوة من خطة المشروع.

وضعان:
- manual (افتراضي، لا يحتاج مفاتيح): يولّد حزمة برومبت كاملة (System Prompt + الدستور + TASK + HANDOFF)
  في projects/<PID>/runs/<step>/prompt.md لتُلصق في Claude/ChatGPT، ثم يُسجَّل المخرج بـ record-output.
- live: يستدعي النموذج عبر طبقة المحوّل ويحفظ المخرج ويسجل الكلفة والتدقيق.
لا يُغيّر الوكيل المخطوط مباشرة؛ المخرجات تُحفظ في runs/ ثم ينقلها المنسق إلى المخزن المسموح.
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

import yaml

from . import audit, protocol, registry as R, state as ST
from .generate import agent_dir
from .ids import now_iso
from .paths import PROMPTS, PROJECTS, ROOT


AUTHOR_ONLY_BEGIN = "<!-- AUTHOR_ONLY:BEGIN -->"
AUTHOR_ONLY_END = "<!-- AUTHOR_ONLY:END -->"


def style_contract(agent_id: str, register: str | None) -> str:
    """عقد الأسلوب: عناصر البصمة **المعتمدة** لسجلّ المشروع من MEM-AUTHOR.
    لا يُحقن إلا للوكلاء الذين يملكون قراءة MEM-AUTHOR (Least Privilege)، ولا تدخل فيه المرشّحات."""
    if not register or "MEM-AUTHOR" not in R.agents()[agent_id]["memory"]["read"]:
        return ""
    from . import knowledge
    try:
        items = knowledge.current("MEM-AUTHOR")
    except FileNotFoundError:
        return ""
    rules = [it for it in items.values() if it["Type"] == "style_rule" and register in it.get("Tags", [])
             and it.get("Approved_By") == "HUMAN-AUTHOR"]
    if not rules:
        return ""
    rules.sort(key=lambda it: it["Memory_ID"])
    lines = [f"- [{it['Memory_ID']} v{it['Version']}] {it['Content']}" for it in rules]
    return (f"\n\n{AUTHOR_ONLY_BEGIN}\nAUTHOR STYLE CONTRACT — register: {register} (approved, MEM-AUTHOR)\n"
            "التزم بهذه الملامح المعتمدة من المؤلف؛ ما يخالفها يُعلَّم للمحرر ولا يُفرض على النص:\n"
            + "\n".join(lines) + f"\n{AUTHOR_ONLY_END}\n")


def compose_system_prompt(agent_id: str, register: str | None = None) -> str:
    a = R.agents()[agent_id]
    sp = (agent_dir(a) / "system_prompt.md").read_text(encoding="utf-8")
    body = re.search(r"```text\n(.*)```", sp, re.S).group(1)
    return body + style_contract(agent_id, register) + "\n\n" + (PROMPTS / "constitution.md").read_text(encoding="utf-8")


def _find_step(plan: dict, step_id: str | None) -> dict:
    if step_id is None:
        s = ST.next_step(plan)
        if s is None:
            raise ValueError("no pending steps")
        return s
    for s in plan["steps"]:
        if s["id"] == step_id:
            return s
    raise KeyError(step_id)


def build_task(pid: str, step: dict) -> tuple[dict, dict]:
    manifest = yaml.safe_load((PROJECTS / pid / "manifest.yaml").read_text(encoding="utf-8"))
    decisions = yaml.safe_load((PROJECTS / pid / "decisions.yaml").read_text(encoding="utf-8"))["decisions"]
    agent = step.get("assigned_agent", step["agent"])
    to = agent if agent not in ("HUMAN-AUTHOR",) else "HUMAN-AUTHOR"
    ctx = (f"المشروع «{manifest['title']}» ({manifest['project_type']}، نموذج {manifest['operating_model']}). "
           f"سير العمل {manifest['workflow']} — الخطوة {step['id']} ({step.get('stage', step.get('task'))}). "
           f"الأطروحة: {manifest.get('thesis') or 'لم تُعتمد بعد'}. أسلوب التوثيق: {manifest['citation_style']}.")
    pkg = protocol.handoff(
        project_id=pid, frm="AG-ORC", to=to, task=step["task"], context=ctx,
        input_files=step.get("inputs", []), decisions=[f"{d['id']}: {d['decision']}" for d in decisions],
        unresolved=[], sources=[], quality_status={"last_gate": step.get("gate"), "status": "PENDING", "open_issues": 0},
        deadline=manifest.get("deadline") or "2099-12-31", expected_output=", ".join(step.get("outputs", [])) or "RESULT وفق OUTPUT CONTRACT",
        workflow_step=step["id"])
    msg = protocol.message(pid, "TASK", "AG-ORC", to, f"{step['id']} {step['task']}",
                           content=yaml.safe_dump(pkg, allow_unicode=True, sort_keys=False),
                           action_required=f"نفّذ {step['task']} وأعد RESULT", handoff_id=pkg["HANDOFF_ID"],
                           decision_level=step.get("decision_level"))
    return pkg, msg


def run_step(pid: str, step_id: str | None = None, live: bool = False, engine: str | None = None) -> Path:
    plan = ST.plan(pid)
    step = _find_step(plan, step_id)
    agent = step.get("assigned_agent", step.get("agent"))
    if step.get("human_approval") and step["status"] != "AWAITING_AUTHOR":
        pass  # يُنفذ العمل ثم ينتظر المؤلف
    pkg, msg = build_task(pid, step)
    protocol.post(pkg, PROJECTS / pid)
    protocol.post(msg, PROJECTS / pid)
    run_dir = PROJECTS / pid / "runs" / step["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    # خطوة يطلب فيها المنسق قرار المؤلف (L4) = مهمة للمؤلف لا للنموذج
    if agent == "AG-ORC" and step.get("human_approval") and step["task"].startswith("request_"):
        agent = "HUMAN-AUTHOR"
    if agent in ("HUMAN-AUTHOR",):
        prev = [s for s in plan["steps"] if s["status"] == "DONE" and (PROJECTS / pid / "runs" / s["id"] / "output.md").exists()]
        latest = f"projects/{pid}/runs/{prev[-1]['id']}/output.md" if prev else "—"
        (run_dir / "author_task.md").write_text(
            f"# مهمة للمؤلف (L4)\n\n{msg['SUBJECT']}\n\n**آخر مُخرَج للمراجعة:** `{latest}`\n\n"
            f"للاعتماد: `rkpos complete {pid} {step['id']} --actor HUMAN-AUTHOR --decision \"…\" --approved-file <الملف>`\n\n"
            f"```yaml\n{msg['CONTENT']}```\n", encoding="utf-8")
        step["status"] = "AWAITING_AUTHOR"
        ST.save_plan(pid, plan)
        ST.refresh(pid)
        return run_dir / "author_task.md"
    from .stylometry import register_for
    system = compose_system_prompt(agent, register_for(pid))
    user = f"TASK MESSAGE\n```yaml\n{yaml.safe_dump(msg, allow_unicode=True, sort_keys=False)}```\n"
    (run_dir / "prompt.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}", encoding="utf-8")
    out_path = run_dir / "prompt.md"
    if live:
        from .adapters import router
        comp, warnings = router.run(agent, system, user, pid, stage=step["id"], engine=engine)
        (run_dir / "warnings.txt").write_text("\n".join(warnings), encoding="utf-8")
        if comp.text:
            (run_dir / "output.md").write_text(comp.text, encoding="utf-8")
            out_path = run_dir / "output.md"
            step["status"] = "AWAITING_AUTHOR" if step.get("human_approval") else "IN_REVIEW"
        elif comp.refused:
            (run_dir / "refusal.txt").write_text(comp.stop_reason or "refusal", encoding="utf-8")
        else:  # المحرّك اليدوي: الحزمة جاهزة للنسخ
            step["status"] = "IN_PROGRESS"
        audit.log(agent, f"run_step:{step['task']}", project=pid, files_changed=[str(out_path.relative_to(ROOT))],
                  model=comp.model)
    else:
        step["status"] = "IN_PROGRESS"
        audit.log("AG-ORC", f"dispatch_manual:{step['id']}", project=pid, files_changed=[str(out_path.relative_to(ROOT))])
    ST.save_plan(pid, plan)
    ST.refresh(pid)
    return out_path


def record_output(pid: str, step_id: str, output_file: Path) -> Path:
    """تسجيل مخرج نُفذ يدوياً في واجهة المحادثة."""
    plan = ST.plan(pid)
    step = _find_step(plan, step_id)
    dst = PROJECTS / pid / "runs" / step_id / "output.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(output_file, dst)
    step["status"] = "AWAITING_AUTHOR" if step.get("human_approval") else "IN_REVIEW"
    ST.save_plan(pid, plan)
    ST.refresh(pid)
    audit.log(step.get("assigned_agent", step.get("agent", "AG-ORC")), f"record_output:{step_id}", project=pid,
              files_changed=[str(dst.relative_to(ROOT))])
    return dst


def complete(pid: str, step_id: str, actor: str, decision_text: str | None = None, approved_file: Path | None = None) -> dict:
    """إغلاق خطوة: L4 لا يغلقها إلا HUMAN-AUTHOR، ويُسجَّل قرار DC-xxx."""
    plan = ST.plan(pid)
    step = _find_step(plan, step_id)
    if step.get("decision_level") == "L4" and actor != "HUMAN-AUTHOR":
        raise PermissionError("L4 step requires HUMAN-AUTHOR")
    dpath = PROJECTS / pid / "decisions.yaml"
    dec = yaml.safe_load(dpath.read_text(encoding="utf-8"))
    entry = None
    if step.get("decision_level") in ("L3", "L4") or decision_text:
        entry = {"id": f"DC-{len(dec['decisions']) + 1:03d}", "date": now_iso(), "step": step_id, "level": step.get("decision_level"),
                 "decision": decision_text or f"اعتماد {step['task']}", "approved_by": actor}
        dec["decisions"].append(entry)
        dpath.write_text(yaml.safe_dump(dec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    files = [str(dpath.relative_to(ROOT))]
    if approved_file:
        if actor != "HUMAN-AUTHOR":
            raise PermissionError("only the author moves text into ST-APPROVED")
        dst = PROJECTS / pid / "manuscript/approved" / approved_file.name
        shutil.copyfile(approved_file, dst)
        files.append(str(dst.relative_to(ROOT)))
    step["status"] = "DONE"
    ST.save_plan(pid, plan)
    st = ST.load(pid)
    if entry:
        st["PINNED_DECISIONS"].append(entry["id"])
    if step.get("gate"):
        st["QUALITY_GATE"] = {"current": step["gate"], "status": f"APPROVED ({entry['id'] if entry else actor})"}
    st["LAST_WORK_POINT"] = f"{step_id} {step['task']}"
    ST.save(pid, st)
    ST.refresh(pid)
    audit.log(actor, f"complete:{step_id}", project=pid, files_changed=files,
              decision=entry["id"] if entry else None, decision_level=step.get("decision_level"), approval=actor)
    return entry or {}


WORKSPACE = ROOT / "workspace"  # تشغيلات خارج المشاريع — غير متتبعة (قد تحمل عقد الأسلوب)


def run_adhoc(agent_id: str, task: str, register: str | None = None, project: str | None = None,
              context: str = "", engine: str | None = "manual") -> dict:
    """تفعيل وكيل مباشرة بتكليف من المؤلف خارج خطة المشروع (لوحة التحكم).
    الضوابط نفسها: برومبت الوكيل + عقد الأسلوب إن كان يقرأ MEM-AUTHOR + الدستور؛ القرار L4 يبقى للمؤلف."""
    from .ids import short_id
    agents = R.agents()
    if agent_id not in agents:
        raise KeyError(agent_id)
    if not task.strip():
        raise ValueError("task is empty")
    if project and not (PROJECTS / project / "manifest.yaml").exists():
        raise KeyError(project)
    if project and not register:
        from .stylometry import register_for
        register = register_for(project)
    system = compose_system_prompt(agent_id, register)
    msg = {"TYPE": "TASK", "FROM": "HUMAN-AUTHOR", "TO": agent_id, "MODE": "ad-hoc (control panel)",
           "PROJECT": project, "REGISTER": register, "TASK": task.strip(), "CONTEXT": context.strip() or None,
           "EXPECTED_OUTPUT": "RESULT وفق OUTPUT CONTRACT في برومبتك؛ ما يحتاج قراراً L4 يُرفع للمؤلف ولا يُحسم"}
    user = f"TASK MESSAGE\n```yaml\n{yaml.safe_dump(msg, allow_unicode=True, sort_keys=False)}```\n"
    rid = short_id("ADH")
    run_dir = (PROJECTS / project / "runs" / rid) if project else (WORKSPACE / "adhoc" / f"{rid}-{agent_id}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompt.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}", encoding="utf-8")
    out = {"run_id": rid, "dir": str(run_dir.relative_to(ROOT)), "system": system, "user": user,
           "output": None, "model": None, "warnings": [], "usd": None}
    if engine != "manual":
        from .adapters import router
        comp, warnings = router.run(agent_id, system, user, project, stage=rid, engine=engine)
        out.update(model=comp.model, warnings=warnings, usd=comp.raw.get("total_cost_usd"))
        if comp.text:
            (run_dir / "output.md").write_text(comp.text, encoding="utf-8")
            out["output"] = comp.text
        elif comp.refused:
            out["warnings"].append(f"REFUSED: {comp.stop_reason}")
    audit.log(agent_id, f"adhoc:{rid}", project=project, files_changed=[out["dir"]], model=out["model"],
              approval="HUMAN-AUTHOR")
    return out
