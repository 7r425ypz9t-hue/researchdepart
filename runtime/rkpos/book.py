"""محرّك بناء العمل: المخطط ← الوحدات ← المسودات ← صوت المؤلف ← الاعتماد ← التجميع.

مستويات الإنتاج (config/production_levels.yaml):
- scaffold: النظام يكتب بطاقات الوحدات، والمؤلف يكتب النص.
- staged:   وحدة بعد وحدة، ولا تُكتب وحدة قبل اعتماد سابقتها (البدء بالمقدمة).
- full:     الكتاب كاملاً بعدد الصفحات المطلوب، ثم مراجعة المؤلف وعودته بالنص إلى صوته.

لكل وحدة تُحفظ مسودة الوكيل الأصلية (Unn.ai.md) فلا تضيع، ويُقاس عليها مقدار تدخل المؤلف
(author_change) — سجلّ صادق لنصيب كل طرف يخدم الإفصاح، لا أداة لإخفائه.
"""
from __future__ import annotations
import difflib
import math
import re
import shutil

import yaml

from . import audit, genres as GN, registry as R
from .ids import now_iso
from .paths import PROJECTS, ROOT

STATUSES = ("PLANNED", "CARDED", "DRAFTED", "REVISED", "APPROVED")
PART_WORDS = 2500           # أقصى طول يُطلب في استدعاء واحد؛ الوحدة الأطول تُكتب على أجزاء متصلة
BEGIN, END = "===BEGIN_TEXT===", "===END_TEXT==="
AR_WORD = re.compile(r"[ء-يA-Za-z0-9]+")


def words(text: str) -> int:
    return len(AR_WORD.findall(text or ""))


# ------------------------------------------------------------------ التخزين
def _p(pid):
    return PROJECTS / pid / "structure/outline.yaml"


def _drafts(pid):
    d = PROJECTS / pid / "manuscript/drafts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(pid: str) -> dict:
    p = _p(pid)
    if not p.exists():
        raise FileNotFoundError(f"{pid}: لا مخطط بناء (structure/outline.yaml)")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def save(pid: str, ob: dict) -> None:
    ob["updated"] = now_iso()
    _p(pid).parent.mkdir(parents=True, exist_ok=True)
    _p(pid).write_text(yaml.safe_dump(ob, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _unit(ob: dict, uid: str) -> tuple[int, dict]:
    for i, u in enumerate(ob["units"]):
        if u["id"] == uid:
            return i, u
    raise KeyError(f"وحدة غير موجودة: {uid}")


def _decision(pid: str, text: str, level: str = "L4") -> str:
    dpath = PROJECTS / pid / "decisions.yaml"
    dec = yaml.safe_load(dpath.read_text(encoding="utf-8"))
    did = f"DC-{len(dec['decisions']) + 1:03d}"
    dec["decisions"].append({"id": did, "date": now_iso(), "step": "BOOK", "level": level, "decision": text,
                             "approved_by": "HUMAN-AUTHOR"})
    dpath.write_text(yaml.safe_dump(dec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return did


def _require_author(actor: str):
    if actor != "HUMAN-AUTHOR":
        raise PermissionError("L4: requires HUMAN-AUTHOR")


# ------------------------------------------------------------------ التهيئة والمخطط
def init(pid: str, level: str, target_pages: int | None, words_per_page: int | None, genre: str) -> dict:
    GN.check_level(genre, level)
    wpp = words_per_page or GN.levels()["words_per_page_default"]
    g = GN.genres()[genre]
    tw = g.get("max_words") if g.get("max_words") else (target_pages * wpp if target_pages else None)
    ob = {"project_id": pid, "genre": genre, "level": level, "target_pages": target_pages, "words_per_page": wpp,
          "target_words": tw, "outline_approved": False, "units": []}
    save(pid, ob)
    return ob


def _distribute(units: list[dict], total: int | None, genre: str) -> None:
    if not total:
        return
    fixed = sum(u["target_words"] for u in units if u.get("target_words"))
    free = [u for u in units if not u.get("target_words")]
    if not free:
        return
    weights = [0.5 if u["kind"] in ("introduction", "conclusion") else 1.0 for u in free]
    rest = max(total - fixed, 50 * len(free))
    for u, w in zip(free, weights):
        u["target_words"] = max(50, int(round(rest * w / sum(weights), -1)))


def skeleton(pid: str, n_units: int) -> dict:
    """مخطط افتراضي بحسب الجنس يحرره المؤلف أو يستبدل به مقترح الوكيل."""
    ob = load(pid)
    g = ob["genre"]
    units = []
    if g == "op_ed":
        units = [{"title": "العمود", "kind": "column", "brief": ""}]
    elif g == "creative":
        units = [{"title": f"الفصل {i}", "kind": "chapter", "brief": ""} for i in range(1, n_units + 1)]
    else:
        units = ([{"title": "المقدمة", "kind": "introduction", "brief": "الإشكالية والأطروحة والمنهج وخريطة المحاور"}]
                 + [{"title": f"المحور {i}", "kind": "axis", "brief": ""} for i in range(1, n_units + 1)]
                 + [{"title": "الخاتمة", "kind": "conclusion", "brief": "النتائج والاقتراحات والأسئلة المفتوحة"}])
    return set_units(pid, units)


def set_units(pid: str, units: list[dict], force: bool = False) -> dict:
    ob = load(pid)
    if not force and any(u["status"] not in ("PLANNED", "CARDED") for u in ob["units"]):
        raise ValueError("بدأت كتابة الوحدات؛ تعديل المخطط بعدها يحتاج force (وقرار المؤلف)")
    clean = []
    for i, u in enumerate(units):
        if not str(u.get("title", "")).strip():
            raise ValueError(f"الوحدة {i + 1} بلا عنوان")
        clean.append({"id": f"U{i:02d}" if ob["genre"] not in ("creative", "op_ed") else f"U{i + 1:02d}",
                      "title": str(u["title"]).strip(), "kind": u.get("kind") or GN.genres()[ob["genre"]]["unit_kind"],
                      "brief": str(u.get("brief") or "").strip(),
                      "target_words": int(u["target_words"]) if u.get("target_words") else None,
                      "status": "PLANNED", "words": 0})
    _distribute(clean, ob["target_words"], ob["genre"])
    ob["units"], ob["outline_approved"] = clean, False
    save(pid, ob)
    return ob


def approve_outline(pid: str, actor: str) -> dict:
    _require_author(actor)
    ob = load(pid)
    if not ob["units"]:
        raise ValueError("المخطط فارغ")
    ob["outline_approved"] = True
    did = _decision(pid, f"اعتماد مخطط البناء ({len(ob['units'])} وحدة، مستوى {ob['level']}، "
                         f"{ob.get('target_words') or '—'} كلمة)")
    save(pid, ob)
    audit.log("HUMAN-AUTHOR", "book_outline_approved", project=pid, files_changed=[str(_p(pid).relative_to(ROOT))],
              decision=did, decision_level="L4", approval="HUMAN-AUTHOR")
    return ob


def polish(pid: str, engine: str, only_flagged: bool = True, progress=None) -> list[str]:
    """ضبط آلي للوحدات (أكاديمي للبحث والفكر، وصوت المؤلف للرأي والسرد) يُعتمد نسخة عمل للوكيل لا للمؤلف."""
    rep = voice_report(pid)
    ids = [r["id"] for r in rep["units"] if r["words"] and r["status"] != "APPROVED" and (r["flag"] or not only_flagged)]
    for i, uid in enumerate(ids):
        if progress:
            progress(i, len(ids), uid)
        r = align_voice(pid, uid, engine)
        record_unit(pid, uid, r["text"], source="aligned")
    return ids


def approve_trivial_outline(pid: str) -> dict:
    """مخطط الوحدة الواحدة (عمود الرأي): لا قرار فيه يملكه المؤلف، فيُثبَّت آلياً (L1) ويُسجَّل."""
    ob = load(pid)
    if len(ob["units"]) != 1:
        raise ValueError("التثبيت الآلي لمخطط الوحدة الواحدة وحده")
    ob["outline_approved"] = True
    save(pid, ob)
    audit.log("AG-ORC", "book_outline_single_unit", project=pid, files_changed=[str(_p(pid).relative_to(ROOT))],
              decision_level="L1")
    return ob


def parse_outline(text: str) -> list[dict]:
    """يستخرج قائمة الوحدات من ردّ الوكيل (كتلة yaml فيها units)."""
    m = re.search(r"```(?:yaml)?\s*\n(.*?)```", text, re.S)
    data = yaml.safe_load(m.group(1) if m else text)
    units = data.get("units") if isinstance(data, dict) else data
    if not isinstance(units, list) or not units:
        raise ValueError("لم أجد قائمة units في الرد")
    return [{"title": u.get("title"), "brief": u.get("brief", ""), "kind": u.get("kind"),
             "target_words": u.get("target_words")} for u in units if isinstance(u, dict)]


def propose_outline(pid: str, engine: str | None = "manual", n_units: int | None = None, guidance: str = "") -> dict:
    """يطلب من وكيل المخطط (مهندس الكتاب أو الكاتب الروائي) مخططاً بالوحدات؛ لا يُعتمد إلا بقرار المؤلف."""
    from .adapters import router
    from .runner import compose_system_prompt
    ob = load(pid)
    m = GN.manifest(pid)
    g = GN.genres()[ob["genre"]]
    agent = g["outline_agent"]
    system = compose_system_prompt(agent, g["register"], ob["genre"])
    kinds = "introduction | axis | conclusion" if ob["genre"] in ("research", "intellectual") else g["unit_kind"]
    user = (f"اقترح مخطط بناء للعمل «{m['title']}» ({g['name_ar']}). الطول الكلي {ob.get('target_words') or '—'} كلمة"
            + (f" (نحو {ob['target_pages']} صفحة)" if ob.get("target_pages") else "")
            + (f"، في نحو {n_units} وحدة" if n_units else "") + ".\n"
            + ("ابدأ بمقدمة واختم بخاتمة، وبينهما محاور متدرجة يبني كل منها على سابقه.\n" if ob["genre"] in ("research", "intellectual") else "")
            + (f"توجيه المؤلف: {guidance}\n" if guidance else "")
            + f"الأطروحة/الفكرة: {m.get('thesis') or 'لم تُعتمد؛ اقترح ولا تحسم'}\n"
            "أعد كتلة yaml واحدة بالصيغة:\n```yaml\nunits:\n  - {title: \"…\", kind: " + kinds.split(" |")[0]
            + ", brief: \"…\", target_words: 0}\n```\nثم سطوراً قليلة تعلّل البناء. target_words اختياري (يُوزَّع آلياً).")
    if engine == "manual":
        return {"manual": True, "text": f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}"}
    comp, warnings = router.run(agent, system, user, pid, stage="BOOK-OUTLINE", engine=engine)
    units = parse_outline(comp.text)
    ob = set_units(pid, units)
    (PROJECTS / pid / "structure/outline_proposal.md").write_text(comp.text, encoding="utf-8")
    audit.log(agent, "book_outline_proposed", project=pid, files_changed=[str(_p(pid).relative_to(ROOT))], model=comp.model)
    return {"manual": False, "outline": ob, "rationale": comp.text.split("```")[-1].strip()[:2000]}


# ------------------------------------------------------------------ البرومبت
def _agent(ob: dict, role: str) -> str:
    return GN.genres()[ob["genre"]][role]


def _unit_text(pid: str, u: dict) -> str:
    d = _drafts(pid)
    for f in (PROJECTS / pid / "manuscript/approved" / f"{u['id']}.md", d / f"{u['id']}.md"):
        if f.exists():
            return f.read_text(encoding="utf-8")
    return ""


def _tail(text: str, n: int) -> str:
    w = text.split()
    return " ".join(w[-n:])


def _context(pid: str, ob: dict, idx: int) -> str:
    m = GN.manifest(pid)
    lines = [f"العمل: «{m['title']}» — {GN.genres()[ob['genre']]['name_ar']} — مستوى الإنتاج: {ob['level']}",
             f"الأطروحة/الفكرة المعتمدة: {m.get('thesis') or 'لم تُعتمد بعد (لا تخترعها؛ اعمل من المخطط)'}",
             f"الطول الكلي المستهدف: {ob.get('target_words') or '—'} كلمة", "", "المخطط المعتمد:"]
    for i, u in enumerate(ob["units"]):
        mark = "◄ الوحدة المطلوبة" if i == idx else u["status"]
        lines.append(f"- {u['id']} {u['title']} ({u['target_words'] or '—'} كلمة) [{mark}] — {u['brief']}")
    bible = PROJECTS / pid / "story_bible.md"
    if ob["genre"] == "creative" and bible.exists():
        lines += ["", "كرّاسة الرواية (ملزمة للاتساق):", bible.read_text(encoding="utf-8")[:12000]]
    prev = [u for u in ob["units"][:idx] if _unit_text(pid, u)]
    if prev:
        lines += ["", "خلاصة ما كُتب قبلها (للاتصال وعدم التكرار):"]
        for u in prev[:-1]:
            t = _unit_text(pid, u).split()
            lines.append(f"[{u['id']} {u['title']}] {' '.join(t[:80])} … {' '.join(t[-60:])}")
        last = prev[-1]
        lines.append(f"[{last['id']} {last['title']} — آخر ما كُتب حرفياً] … {_tail(_unit_text(pid, last), 600)}")
    return "\n".join(lines)


def unit_messages(pid: str, uid: str, part: int = 1, parts: int = 1, so_far: str = "",
                  guidance: str = "") -> tuple[str, str, str]:
    from .runner import compose_system_prompt
    ob = load(pid)
    idx, u = _unit(ob, uid)
    agent = _agent(ob, "lead_agent")
    g = GN.genres()[ob["genre"]]
    system = compose_system_prompt(agent, g["register"], ob["genre"])
    if ob["level"] == "scaffold":
        task = (f"اكتب «بطاقة الوحدة» {u['id']} «{u['title']}» لا نصها: الفكرة المركزية، الحجج أو المشاهد بالترتيب، "
                "الشواهد والمصادر المطلوبة ([NEEDS-EVIDENCE] لما ليس في السجل)، الأسئلة التي يحسمها المؤلف، "
                f"وموازنة الطول ({u['target_words'] or '—'} كلمة). المؤلف سيكتب النص بنفسه.")
    else:
        target = int((u["target_words"] or 800) / parts)
        task = (f"اكتب نص الوحدة {u['id']} «{u['title']}» كاملاً بصوت المؤلف وصفات الجنس، نحو {target} كلمة"
                + (f" (الجزء {part} من {parts}؛ تابع بلا تكرار ولا تمهيد جديد" + ("، واختم الوحدة." if part == parts else "، ولا تختم.") + ")" if parts > 1 else "")
                + f". موجز الوحدة: {u['brief'] or 'من المخطط'}.")
    fmt = (f"اكتب النص وحده بين السطرين {BEGIN} و{END} بلا تعليق داخله؛ وبعد {END} اكتب ملاحظاتك "
           "(ما يحتاج دليلاً، ما يحتاج قرار المؤلف، اقتراحات الكرّاسة) في قسم NOTES.")
    user = f"{_context(pid, ob, idx)}\n\n" + (f"ما كُتب من هذه الوحدة حتى الآن (آخره):\n{_tail(so_far, 800)}\n\n" if so_far else "") \
        + (f"توجيه المؤلف (ملزم):\n{guidance}\n\n" if guidance else "") \
        + f"المهمة:\n{task}\n\nالصيغة:\n{fmt}\n"
    return agent, system, user


def extract(text: str) -> tuple[str, str]:
    if BEGIN in text:
        body = text.split(BEGIN, 1)[1]
        body, _, notes = body.partition(END)
        return body.strip(), notes.strip()
    return text.strip(), ""


# ------------------------------------------------------------------ التشغيل
def _check_sequence(ob: dict, idx: int, relax: bool = False) -> None:
    if not ob["outline_approved"]:
        raise PermissionError("المخطط لم يُعتمد بعد (L4)")
    seq = GN.levels()["levels"][ob["level"]]["sequence"]
    if relax and seq == "strict":      # الوضع المباشر: الترتيب للاتساق، دون انتظار اعتماد كل وحدة
        seq = "drafted"
    if idx == 0 or seq == "free":
        return
    prev = ob["units"][idx - 1]
    if seq == "strict" and prev["status"] != "APPROVED":
        raise PermissionError(f"المستوى التدرّجي: اعتمدوا {prev['id']} «{prev['title']}» أولاً")
    if seq == "drafted" and prev["status"] not in ("DRAFTED", "REVISED", "APPROVED"):
        raise PermissionError(f"اكتبوا {prev['id']} أولاً (الاتساق يقتضي الترتيب)")


def _measure(pid: str, ob: dict, text: str) -> dict:
    """جنس بصمة (رأي/سرد): القرب من صوت المؤلف. جنس علمي/فكري: مؤشرات الانضباط الأكاديمي."""
    from . import stylometry as S
    from . import sanitize as SZ
    if words(text) < 60:
        return {}
    reg = GN.genres()[ob["genre"]]["register"]
    human = SZ.humanlang_report(text)
    if not GN.author_voice(ob["genre"]):
        return {"register": reg, "discipline": GN.discipline_report(text), "human": human}
    ref, assisted = S.load_reference(reg), S.load_assisted_pole()
    if not ref:
        return {"register": reg, "human": human}
    prof = S.profile(text)
    out = {"register": reg, "human": human}
    if assisted and reg in S.POLE_REGISTERS:
        out["pole"] = S.pole(prof, ref, assisted)
    else:
        dev = S.distance(prof, ref)
        out["deviation_mean"] = round(sum(abs(v) for v in dev.values() if v is not None) / max(len(dev), 1), 2)
    return out


def draft_unit(pid: str, uid: str, engine: str | None = "manual", guidance: str = "", relax: bool = False) -> dict:
    ob = load(pid)
    idx, u = _unit(ob, uid)
    _check_sequence(ob, idx, relax)
    if u["status"] == "APPROVED":
        raise ValueError(f"{uid} معتمدة؛ لا تُعاد كتابتها")
    from .adapters import router
    tw = u["target_words"] or 800
    parts = 1 if ob["level"] == "scaffold" else max(1, math.ceil(tw / PART_WORDS))
    run_dir = PROJECTS / pid / "runs" / f"BOOK-{uid}"
    run_dir.mkdir(parents=True, exist_ok=True)
    if engine == "manual":
        agent, system, user = unit_messages(pid, uid, 1, 1, guidance=guidance)
        (run_dir / "prompt.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}", encoding="utf-8")
        return {"unit": uid, "manual": True, "path": str((run_dir / "prompt.md").relative_to(ROOT)),
                "text": f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}"}
    body, notes, models, usd = "", [], set(), 0.0
    for k in range(1, parts + 1):
        agent, system, user = unit_messages(pid, uid, k, parts, body, guidance=guidance)
        comp, warnings = router.run(agent, system, user, pid, stage=f"BOOK-{uid}" + (f" ({k}/{parts})" if parts > 1 else ""),
                                    engine=engine)
        if comp.refused or not comp.text:
            raise RuntimeError(f"{uid}: لم يُرجع المحرّك نصاً ({comp.stop_reason}); {warnings}")
        t, n = extract(comp.text)
        body = (body + "\n\n" + t).strip()
        notes.append(n)
        models.add(comp.model)
        usd += float(comp.raw.get("total_cost_usd") or 0)
    return record_unit(pid, uid, body, source="ai", notes="\n\n".join(x for x in notes if x), models=sorted(models), usd=usd)


def record_unit(pid: str, uid: str, text: str, source: str = "ai", notes: str = "", models=None, usd: float = 0.0) -> dict:
    """تسجيل نص وحدة: من الوكيل (ai، يُحفظ أصلاً) أو بقلم المؤلف (author)."""
    ob = load(pid)
    idx, u = _unit(ob, uid)
    if not text.strip():
        raise ValueError("نص فارغ")
    from . import sanitize as SZ
    text = SZ.source(text)              # لا محارف خفية في الأصل المحفوظ
    d = _drafts(pid)
    card = ob["level"] == "scaffold" and source == "ai"
    if card:
        (d / f"{uid}.card.md").write_text(text, encoding="utf-8")
        u["status"] = "CARDED"
    else:
        (d / f"{uid}.md").write_text(text, encoding="utf-8")
        if source == "ai":
            (d / f"{uid}.ai.md").write_text(text, encoding="utf-8")
        u["status"] = "REVISED" if source == "author" else "DRAFTED"   # aligned: ضبط آلي يبقى مسودة وكيل
        u["words"] = words(text)
        u["voice"] = _measure(pid, ob, text)
        u["author_change"] = change_ratio(pid, uid)
    if notes:
        (d / f"{uid}.notes.md").write_text(notes, encoding="utf-8")
    u["source"] = source
    save(pid, ob)
    audit.log(_agent(ob, "lead_agent") if source != "author" else "HUMAN-AUTHOR", f"book_{'card' if card else 'draft'}:{uid}",
              project=pid, files_changed=[f"projects/{pid}/manuscript/drafts/{uid}{'.card' if card else ''}.md"],
              model=", ".join(models or []) or None, cost_usd=round(usd, 6) if usd else None)
    return {"unit": uid, "status": u["status"], "words": u.get("words", words(text)), "voice": u.get("voice"),
            "target_words": u["target_words"], "notes": notes}


def revise_unit(pid: str, uid: str, text: str) -> dict:
    """تعديل المؤلف لنص الوحدة (يبقى أصل الوكيل محفوظاً للمقارنة)."""
    return record_unit(pid, uid, text, source="author")


def change_ratio(pid: str, uid: str) -> float | None:
    """نسبة ما غيّره المؤلف من مسودة الوكيل (0 = لم يغيّر، 1 = أعاد الكتابة كلها)."""
    d = _drafts(pid)
    ai = d / f"{uid}.ai.md"
    cur = PROJECTS / pid / "manuscript/approved" / f"{uid}.md"
    cur = cur if cur.exists() else d / f"{uid}.md"
    if not ai.exists() or not cur.exists():
        return None
    a, b = ai.read_text(encoding="utf-8").split(), cur.read_text(encoding="utf-8").split()
    return round(1 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 3)


HUMAN_TASK = ("واضبط اللغة البشرية: اكتب كل ملاحظة داخل النص بالعربية بين قوسين (مع إبقاء أسماء الوسوم المعيارية "
              "مثل [FACT] و[NEEDS-EVIDENCE] كما هي وكتابة ما بعدها بالعربية)، وترجم إلى العربية كل ملاحظة إنجليزية، "
              "واستبدل الشَّرطة الطويلة (—) بأدوات الوصل العربية، واحذف اللوازم الجاهزة{hits}. ")
VOICE_TASK = ("أعد صياغة النص التالي ليقترب من صوت المؤلف كما في عقد الأسلوب المعتمد، مع الحفاظ التام على المضمون "
              "والحجج والوقائع والوسوم والإحالات؛ لا تضف معلومة ولا تحذف فكرة. عالج تحديداً: {hints}. {human}"
              f"اكتب النص المعدّل وحده بين {BEGIN} و{END}، ثم اذكر بعد {END} أهم ما غيّرته.")


def _hints(voice: dict) -> str:
    h = ["طول الجمل وتوزيعها", "الوصل بالواو والفاصلة بدل التقطيع", "تقليل النقطتين والقوالب التفسيرية", "التشكيل للضرورة فقط"]
    return "، ".join(h)


DISCIPLINE_TASK = ("أعد ضبط النص التالي ضبطاً أكاديمياً: احذف الإنشاء والحكايات والذكريات والأمثلة غير اللازمة "
                   "والأسئلة البلاغية والتعجب وعبارات القطع، واجعل الجمل خبرية دقيقة والمصطلحات ثابتة، مع الحفاظ التام "
                   "على المضمون والحجج والوسوم والإحالات؛ لا تضف معلومة. {human}"
                   f"اكتب النص المضبوط وحده بين {BEGIN} و{END}، ثم اذكر بعد {END} أهم ما حذفته أو عدّلته.")


def align_voice(pid: str, uid: str, engine: str | None = None) -> dict:
    """مواءمة الصوت (الرأي والسرد) أو الضبط الأكاديمي (البحث والفكر): اقتراح يُقاس قبله وبعده، والمؤلف يختار."""
    from .adapters import router
    from .runner import compose_system_prompt
    ob = load(pid)
    _, u = _unit(ob, uid)
    text = _unit_text(pid, u)
    if not text:
        raise ValueError(f"{uid} بلا نص")
    agent = _agent(ob, "voice_agent")
    reg = GN.genres()[ob["genre"]]["register"]
    system = compose_system_prompt(agent, reg, ob["genre"])
    hits = ((u.get("voice") or {}).get("human") or {}).get("hits") or {}
    found = [x for k in ("stock_phrases", "latin_notes") for x in hits.get(k, [])]
    human = HUMAN_TASK.format(hits=("، ومنها في هذا النص: " + "، ".join(f"«{x}»" for x in found[:10])) if found else "")
    task = (VOICE_TASK.format(hints=_hints(u.get("voice") or {}), human=human) if GN.author_voice(ob["genre"])
            else DISCIPLINE_TASK.format(human=human))
    user = task + f"\n\nالنص:\n{text}"
    if engine == "manual":
        return {"unit": uid, "manual": True, "text": f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}"}
    comp, warnings = router.run(agent, system, user, pid, stage=f"VOICE-{uid}", engine=engine)
    new, notes = extract(comp.text)
    if not new:
        raise RuntimeError(f"لم يُرجع المحرّك نصاً: {warnings}")
    (_drafts(pid) / f"{uid}.aligned.md").write_text(new, encoding="utf-8")
    audit.log(agent, f"book_voice_align:{uid}", project=pid, files_changed=[f"projects/{pid}/manuscript/drafts/{uid}.aligned.md"],
              model=comp.model)
    return {"unit": uid, "before": u.get("voice"), "after": _measure(pid, ob, new), "text": new, "notes": notes}


def approve_unit(pid: str, uid: str, actor: str, text: str | None = None) -> dict:
    _require_author(actor)
    ob = load(pid)
    _, u = _unit(ob, uid)
    if text:
        record_unit(pid, uid, text, source="author")
        ob = load(pid)
        _, u = _unit(ob, uid)
    body = (_drafts(pid) / f"{uid}.md")
    if not body.exists():
        raise ValueError(f"{uid} بلا نص يُعتمد")
    dst = PROJECTS / pid / "manuscript/approved" / f"{uid}.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(body, dst)
    u["status"] = "APPROVED"
    u["author_change"] = change_ratio(pid, uid)
    did = _decision(pid, f"اعتماد الوحدة {uid} «{u['title']}» ({u.get('words')} كلمة؛ تعديل المؤلف {u['author_change']})")
    save(pid, ob)
    audit.log("HUMAN-AUTHOR", f"book_approve:{uid}", project=pid, files_changed=[str(dst.relative_to(ROOT))],
              decision=did, decision_level="L4", approval="HUMAN-AUTHOR")
    return {"unit": uid, "decision": did, "author_change": u["author_change"]}


def estimate(pid: str) -> dict:
    """تقدير كلفة الكتابة الكاملة قبل الإقرار (تقريبي ومعلن الافتراضات)."""
    from . import cost as C
    from .adapters import router
    ob = load(pid)
    todo = [u for u in ob["units"] if u["status"] in ("PLANNED", "CARDED")]
    out_words = sum(u["target_words"] or 800 for u in todo)
    calls = sum(max(1, math.ceil((u["target_words"] or 800) / PART_WORDS)) for u in todo)
    tier = R.agents()[_agent(ob, "lead_agent")]["model_tier"]
    spec = router.candidates(tier)[0]
    p = C.price(spec) or {}
    tin, tout = calls * 15000, int(out_words * 2.5)
    usd = round(tin / 1e6 * p.get("input_per_mtok", 0) + tout / 1e6 * p.get("output_per_mtok", 0), 2) if p else None
    budget = GN.manifest(pid).get("budget_usd")
    return {"units": len(todo), "calls": calls, "words": out_words, "pages": round(out_words / ob["words_per_page"]),
            "model_reference": spec, "usd_estimate": usd, "budget_usd": budget,
            "over_budget": bool(usd and budget and usd > budget),
            "assumptions": "≈15 ألف رمز إدخال لكل استدعاء، و2.5 رمز لكل كلمة عربية مخرجة، بأسعار config/pricing.yaml؛ "
                           "في Claude Code باشتراك تُخصم من حصة الاشتراك لا من رصيد مباشر"}


def draft_all(pid: str, engine: str, progress=None, guidance: str = "", direct: bool = False, redo: bool = False) -> dict:
    """direct: الوضع المباشر يكتب الوحدات كلها تباعاً في المستويين التدرّجي والكامل؛ redo: يعيد كتابة غير المعتمد."""
    ob = load(pid)
    if ob["level"] != "full" and not (direct and ob["level"] == "staged"):
        raise PermissionError("الكتابة الكاملة دفعة واحدة لمستوى «الكامل» وحده")
    if engine == "manual":
        raise ValueError("الكتابة الكاملة تحتاج محرّكاً آلياً (Claude Code أو API)")
    done = []
    todo = [u["id"] for u in ob["units"] if u["status"] in (("PLANNED", "CARDED", "DRAFTED", "REVISED") if redo else ("PLANNED", "CARDED"))]
    for i, uid in enumerate(todo):
        if progress:
            progress(i, len(todo), uid)
        done.append(draft_unit(pid, uid, engine, guidance=guidance, relax=direct))
    if progress:
        progress(len(todo), len(todo), None)
    return {"drafted": done, "assembled": assemble(pid)}


def assemble(pid: str) -> dict:
    """تجميع الكتاب بالترتيب: النص المعتمد إن وُجد، وإلا آخر مسودة؛ مع ملف Word منقّى بهوية الإدارة."""
    ob = load(pid)
    m = GN.manifest(pid)
    parts, missing = [f"# {m['title']}\n\n{m['author']}\n"], []
    for u in ob["units"]:
        t = _unit_text(pid, u)
        if not t:
            missing.append(u["id"])
            continue
        body = t if t.lstrip().startswith("#") else f"## {u['title']}\n\n{t}"
        parts.append(body)
    out = PROJECTS / pid / "manuscript/book_full.md"
    text = "\n\n".join(parts) + "\n"
    out.write_text(text, encoding="utf-8")
    res = {"path": str(out.relative_to(ROOT)), "words": words(text), "pages": round(words(text) / ob["words_per_page"]),
           "target_pages": ob.get("target_pages"), "missing": missing,
           "approved": sum(1 for u in ob["units"] if u["status"] == "APPROVED"), "units": len(ob["units"])}
    try:   # ملف Word منقّى بهوية الإدارة، دون حاجة إلى برامج خارجية
        from . import institution as INS
        from .export import to_docx
        docx = out.with_suffix(".docx")
        from .footnotes import project_sources
        docx.write_bytes(to_docx(text, m["title"], theme=INS.theme(INS.division_of_project(m)), author=m.get("author", ""),
                                 sources=project_sources(pid)))
        res["docx"] = str(docx.relative_to(ROOT))
    except ImportError:
        pass
    audit.log("AG-PUB", "book_assemble", project=pid, files_changed=[res["path"]])
    return res


def voice_report(pid: str) -> dict:
    ob = load(pid)
    rows = []
    for u in ob["units"]:
        v = u.get("voice") or {}
        share = (v.get("pole") or {}).get("assisted_share")
        disc = v.get("discipline") or {}
        human = v.get("human") or {}
        rows.append({"id": u["id"], "title": u["title"], "status": u["status"], "words": u.get("words", 0),
                     "target_words": u["target_words"], "assisted_share": share, "deviation_mean": v.get("deviation_mean"),
                     "discipline_flags": disc.get("flags", []), "human_flags": human.get("flags", []), "author_change": change_ratio(pid, u["id"]),
                     "flag": bool(share is not None and share > 0.5) or bool(disc.get("flags")) or bool(human.get("flags"))})
    written = [r for r in rows if r["words"]]
    ch = [r["author_change"] for r in written if r["author_change"] is not None]
    return {"units": rows, "total_words": sum(r["words"] for r in rows), "target_words": ob.get("target_words"),
            "author_change_mean": round(sum(ch) / len(ch), 3) if ch else None,
            "flagged": [r["id"] for r in rows if r["flag"]],
            "note": ("assisted_share: 0 = صوت المؤلف، 1 = الصياغة المُعانة" if GN.author_voice(ob["genre"]) else
                     "discipline_flags: ما تجاوز حدّ الانضباط الأكاديمي (سرد، أمثلة، ضمير المتكلم، توكيد، تعجب، أسئلة بلاغية)")
                    + "؛ human_flags: لوازم الصياغة الآلية أو الشَّرطة الطويلة أو ملاحظات إنجليزية"
                    + "؛ author_change: نصيب تعديل المؤلف من مسودة الوكيل"}
