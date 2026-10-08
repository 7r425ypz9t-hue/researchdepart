"""الأجناس الكتابية ومستويات الإنتاج (config/genres.yaml · config/production_levels.yaml)."""
from __future__ import annotations

import yaml

from . import registry as R
from .paths import CONFIG, PROJECTS


VOICE_REGISTERS = {"essay", "narrative"}   # سجلّات تُطبَّق فيها بصمة المؤلف (مقال الرأي والسرد)


def genres() -> dict:
    return R.load_yaml(CONFIG / "genres.yaml")["genres"]


def levels() -> dict:
    return R.load_yaml(CONFIG / "production_levels.yaml")


def genre_for_type(project_type: str, override: str | None = None) -> str:
    g = genres()
    if override:
        if override not in g:
            raise ValueError(f"unknown genre {override}")
        return override
    for gid, spec in g.items():
        if project_type in spec["project_types"]:
            return gid
    cross = R.load_yaml(CONFIG / "genres.yaml").get("cross_genre", {})
    if project_type in cross:
        return cross[project_type]
    raise ValueError(f"no genre for project type {project_type}")


def manifest(pid: str) -> dict:
    return yaml.safe_load((PROJECTS / pid / "manifest.yaml").read_text(encoding="utf-8"))


def genre_of(pid: str) -> str:
    m = manifest(pid)
    return m.get("genre") or genre_for_type(m["project_type"])


def check_level(genre: str, level: str) -> None:
    allowed = genres()[genre]["levels"]
    if level not in allowed:
        raise ValueError(f"المستوى {level} غير متاح لجنس {genre}؛ المتاح: {allowed}")


def profile_block(genre: str | None) -> str:
    """كتلة «صفات الجنس» تُضاف إلى برومبت الوكيل؛ قواعد صنعة عامة لا مواد خاصة بالمؤلف."""
    if not genre:
        return ""
    g = genres()[genre]
    lines = [f"\n\nGENRE PROFILE — {g['name_ar']} ({g['name_en']})",
             "الصفات الفكرية:", *[f"- {x}" for x in g["intellectual"]],
             "الصفات الأسلوبية:", *[f"- {x}" for x in g["stylistic"]],
             f"الأدلة والتوثيق: {g['evidence']}",
             "محظورات الجنس:", *[f"- {x}" for x in g["prohibited"]]]
    if g.get("max_words"):
        lines.append(f"سقف الطول: {g['max_words']} كلمة.")
    if not g.get("author_voice", True):
        lines += ["ACADEMIC DISCIPLINE — لا تُطبَّق هنا البصمة الشخصية للمؤلف؛ الحاكم هو الانضباط العلمي:",
                  *[f"- {x}" for x in discipline()["rules"]]]
    return "\n".join(lines) + "\n"


def discipline() -> dict:
    return R.load_yaml(CONFIG / "genres.yaml")["discipline"]


def author_voice(genre: str | None) -> bool:
    return bool(genre) and bool(genres()[genre].get("author_voice", True))


def discipline_report(text: str) -> dict:
    """قياس الانضباط الأكاديمي: مؤشرات الإنشاء والسرد والأمثلة والتوكيد لكل ألف كلمة، مع ما تجاوز حدّه."""
    import re
    words = max(len(re.findall(r"[\u0621-\u064A]+", text)), 1)
    out, flags = {}, []
    for name, c in discipline()["checks"].items():
        n = sum(text.count(p) for p in c.get("patterns", [])) + sum(text.count(ch) for ch in c.get("chars", []))
        per_k = round(1000 * n / words, 2)
        out[name] = per_k
        if per_k > c["max"]:
            flags.append(name)
    return {"per_1k": out, "flags": flags, "ok": not flags}
