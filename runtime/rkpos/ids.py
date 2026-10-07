"""توليد المعرّفات الموحدة."""
from __future__ import annotations
import datetime as dt
import re
import uuid

from .paths import PROJECTS


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")


def short_id(prefix: str) -> str:
    return f"{prefix}-{_stamp()}-{uuid.uuid4().hex[:8]}"


def next_project_id(year: int | None = None, projects_dir=PROJECTS) -> str:
    year = year or dt.date.today().year
    pat = re.compile(rf"^RKP-{year}-(\d{{4}})")
    nums = [int(m.group(1)) for p in projects_dir.glob(f"RKP-{year}-*") if (m := pat.match(p.name))]
    return f"RKP-{year}-{(max(nums) + 1 if nums else 1):04d}"


def slugify(text: str, max_len: int = 40) -> str:
    """slug لاتيني إن أمكن، وإلا معرّف قصير ثابت."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:max_len] or "project"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
