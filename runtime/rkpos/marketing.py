"""إدارتا التسويق والتصميم: حزمة تعريفية صادقة وموجز تصميم بهوية الإدارة — للأعمال المعتمدة وحدها."""
from __future__ import annotations

from . import audit, genres as GN, institution as INS
from .paths import PROJECTS, ROOT


def _approved_text(pid: str) -> str:
    root = PROJECTS / pid
    full = root / "manuscript/book_full.md"
    approved = sorted((root / "manuscript/approved").glob("*.md")) if (root / "manuscript/approved").exists() else []
    if not approved:
        raise PermissionError("التسويق للأعمال المعتمدة وحدها: اعتمدوا النص أولاً")
    return full.read_text(encoding="utf-8") if full.exists() else "\n\n".join(f.read_text(encoding="utf-8") for f in approved)


def _run(pid, agent, task, text, engine, stage):
    from .adapters import router
    from .runner import compose_system_prompt
    m = GN.manifest(pid)
    div = INS.divisions()[INS.division_of_project(m)]
    th = INS.theme(div["id"])
    system = compose_system_prompt(agent)
    user = (f"العمل: «{m['title']}» — {m['author']} — {div['name_ar']} ({m['project_type']}).\n"
            f"هوية الإدارة: اللون الرئيس {th['primary']}، اللون المساند {th['accent']}، الخط Noto Naskh Arabic.\n\n"
            f"المهمة:\n{task}\n\nالنص المعتمد (للاستخلاص فقط؛ لا تذكر إلا ما فيه):\n{text[:30000]}\n")
    comp, _ = router.run(agent, system, user, pid, stage=stage, engine=engine)
    return comp.text


def pack(pid: str, engine: str) -> dict:
    if engine in (None, "manual"):
        raise ValueError("حزمة التسويق تحتاج محرّكاً آلياً")
    text = _approved_text(pid)
    out = PROJECTS / pid / "marketing"
    out.mkdir(parents=True, exist_ok=True)
    mk = _run(pid, "AG-MKT", "أعد حزمة تسويق صادقة: (1) ملخص تعريفي في 80 كلمة، (2) نبذة الغلاف الخلفي في 150 كلمة، "
              "(3) بياناً صحفياً قصيراً، (4) خمسة منشورات تواصل قصيرة، (5) خطة إطلاق موجزة (الجمهور، القنوات، التوقيت). "
              "لا مبالغة ولا ادعاء جوائز أو أرقام؛ كل جملة تطابق مضمون النص.", text, engine, "MARKETING")
    (out / "pack.md").write_text(mk, encoding="utf-8")
    ds = _run(pid, "AG-DSN", "اكتب موجز تصميم الغلاف وفق هوية الإدارة: الفكرة البصرية، والألوان (بالرموز)، والخط، والتكوين، "
              "والعناصر وحقوقها. واقترح موجز إخراج داخلي مختصراً.", text, engine, "DESIGN")
    (out / "design_brief.md").write_text(ds, encoding="utf-8")
    audit.log("AG-MKT", "marketing_pack", project=pid, files_changed=[str((out / "pack.md").relative_to(ROOT)),
                                                                      str((out / "design_brief.md").relative_to(ROOT))])
    return {"pack": str((out / "pack.md").relative_to(ROOT)), "design": str((out / "design_brief.md").relative_to(ROOT))}
