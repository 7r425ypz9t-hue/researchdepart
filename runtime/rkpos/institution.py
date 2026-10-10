"""مؤسسة «باحث»: الإدارات التخصصية والمساندة، وهوية كل إدارة التصميمية، والضوابط العامة (config/institution.yaml)."""
from __future__ import annotations

from . import registry as R
from .paths import CONFIG


def config() -> dict:
    return R.load_yaml(CONFIG / "institution.yaml")


def divisions() -> dict[str, dict]:
    return {d["id"]: d for d in config()["divisions"]}


def specialized() -> dict[str, dict]:
    return {k: v for k, v in divisions().items() if v["kind"] == "specialized"}


def division_for_type(project_type: str) -> str:
    for did, d in specialized().items():
        if project_type in d.get("project_types", []):
            return did
    raise ValueError(f"لا إدارة لنوع العمل {project_type}")


def theme(division_id: str | None) -> dict:
    """ألوان الإدارة (من نظام التصميم المركزي)؛ وعند غياب الإدارة: هوية المؤسسة."""
    c = config()
    base = {**c["design_system"]["institution"], "emblem": "§"}
    if division_id and division_id in divisions():
        base.update(divisions()[division_id].get("theme", {}))
    return base


def division_of_project(manifest: dict) -> str | None:
    return manifest.get("division") or (division_for_type(manifest["project_type"])
                                        if manifest.get("project_type") else None)


def check() -> list[str]:
    """اتساق الهيكل المؤسسي: كل نوع عمل في إدارة واحدة، والوكلاء والمهارات معرّفة، ولكل إدارة هوية."""
    errs = []
    A, S = R.agents(), R.skills()
    seen: dict[str, str] = {}
    for did, d in divisions().items():
        for k in ("primary", "accent", "light"):
            if k not in d.get("theme", {}):
                errs.append(f"{did}: theme.{k} missing")
        for a in d.get("lead_agents", []):
            if a not in A:
                errs.append(f"{did}: unknown agent {a}")
        for s in d.get("skills", []):
            if s not in S:
                errs.append(f"{did}: unknown skill {s}")
        for t in d.get("project_types", []):
            if t in seen:
                errs.append(f"project type {t} in two divisions ({seen[t]}, {did})")
            seen[t] = did
    for s in config()["general"]["skills"]:
        if s not in S:
            errs.append(f"general: unknown skill {s}")
    from .genres import genres
    all_types = {t for g in genres().values() for t in g["project_types"]} | set(
        R.load_yaml(CONFIG / "genres.yaml").get("cross_genre", {}))
    for t in sorted(all_types - set(seen)):
        errs.append(f"project type {t} has no division")
    covered = set(config().get("cross_cutting_agents", [])) | {a for d in divisions().values() for a in d.get("lead_agents", [])}
    for a in sorted(set(A) - covered):
        errs.append(f"agent {a} belongs to no division")
    return errs
