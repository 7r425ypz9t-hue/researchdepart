"""خزنة الأصول — نسخة أصلية لا تُعدَّل، وبصمة SHA-256، وفحص السلامة، والنسخ الاحتياطي.

- يُحفظ كل أصل (وثيقة، صورة، تسجيل، بيانات) بمسار مشتق من بصمته: originals/<أول حرفين>/<البصمة><الامتداد>،
  ويُجعل للقراءة فقط؛ وإيداع الملف نفسه مرة ثانية لا يُنشئ نسخة ثانية.
- السجل ملف JSONL واحد (registry.jsonl) بمعرّفات AST-YYYY-NNNN، ولا قاعدة بيانات.
- الخزنة تحت workspace/vault (غير متتبعة في المستودع)، فلا تُرفع الملفات الثنائية أبداً؛
  ويمكن تغيير موضعها بمتغير البيئة RKPOS_VAULT.
- النسخة الاحتياطية ملف zip على نمط BagIt المبسط: السجل والأصول وبيان البصمات وbag-info.txt.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import mimetypes
import os
import stat
import zipfile
from pathlib import Path

from . import audit
from .ids import now_iso
from .paths import ROOT, PROJECTS

KINDS = {"audio": (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"), "video": (".mp4", ".mov", ".mkv", ".avi"),
         "image": (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif"),
         "document": (".pdf", ".docx", ".doc", ".txt", ".md", ".odt", ".rtf", ".epub"),
         "data": (".csv", ".json", ".jsonl", ".geojson", ".xlsx", ".yaml", ".bib")}
KIND_AR = {"audio": "تسجيل صوتي", "video": "تسجيل مرئي", "image": "صورة", "document": "وثيقة", "data": "بيانات", "other": "أخرى"}
INTEGRITY_AR = {"ok": "سليم", "missing": "مفقود", "altered": "معدَّل"}
MAX_BYTES = 512 * 1024 * 1024


def vault_dir() -> Path:
    return Path(os.environ.get("RKPOS_VAULT") or ROOT / "workspace" / "vault")


def registry_path() -> Path:
    return vault_dir() / "registry.jsonl"


def backups_dir() -> Path:
    return vault_dir().parent / "backups"


def kind_of(name: str) -> str:
    ext = Path(name).suffix.lower()
    for k, exts in KINDS.items():
        if ext in exts:
            return k
    return "other"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load() -> list[dict]:
    p = registry_path()
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _save(rows: list[dict]) -> None:
    """إعادة كتابة ذرية للسجل (لتحديث حالة السلامة وتاريخ آخر فحص)."""
    p = registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".jsonl.part")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    os.replace(tmp, p)


def _next_id(rows: list[dict], year: int | None = None) -> str:
    year = year or dt.date.today().year
    pre = f"AST-{year}-"
    nums = [int(r["id"][len(pre):]) for r in rows if r.get("id", "").startswith(pre)]
    return f"{pre}{(max(nums) + 1 if nums else 1):04d}"


def path_of(asset: dict) -> Path:
    return vault_dir() / asset["vault_path"]


def add_bytes(filename: str, data: bytes, *, project: str | None = None, provenance: str = "", rights: str = "",
              depositor: str = "HUMAN-AUTHOR") -> dict:
    """يحفظ الأصل في الخزنة بمساره المشتق من بصمته، للقراءة فقط، ويسجّله. تكرار الملف نفسه يعيد سجله القائم."""
    if not data:
        raise ValueError("الملف فارغ")
    if len(data) > MAX_BYTES:
        raise ValueError("الملف أكبر من الحد المسموح للخزنة (512 ميغابايت)")
    if project and not (PROJECTS / project / "manifest.yaml").exists():
        raise ValueError(f"مشروع غير موجود: {project}")
    h = hashlib.sha256(data).hexdigest()
    ext = Path(filename).suffix.lower()[:10]
    rel = Path("originals") / h[:2] / f"{h}{ext}"
    dest = vault_dir() / rel
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        os.chmod(dest, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    rows = load()
    for r in rows:
        if r["sha256"] == h:
            return {**r, "duplicate": True}
    ts = now_iso()
    row = {"id": _next_id(rows), "sha256": h, "filename": Path(filename).name, "size": len(data),
           "mime": mimetypes.guess_type(filename)[0] or "application/octet-stream", "kind": kind_of(filename),
           "vault_path": rel.as_posix(), "project": project or None, "provenance": provenance or "",
           "rights": rights or "", "depositor": depositor or "HUMAN-AUTHOR", "created_at": ts,
           "integrity": "ok", "last_verified": ts}
    rows.append(row)
    _save(rows)
    audit.log("HUMAN-AUTHOR", "vault_add", project, files_changed=[f"vault:{row['id']}"],
              decision=f"إيداع {row['id']} ({h[:12]})")
    return row


def add(path: Path | str, **kw) -> dict:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"ملف غير موجود: {p}")
    return add_bytes(p.name, p.read_bytes(), **kw)


def verify_all() -> dict:
    """يعيد حساب البصمة لكل أصل ويقارنها بالمسجّل؛ ويعلّم المفقود والمعدَّل (مؤشر «سلامة الأصول الرقمية»)."""
    rows = load()
    report = {"total": len(rows), "ok": 0, "missing": [], "altered": [], "checked_at": now_iso()}
    for a in rows:
        p = path_of(a)
        if not p.exists():
            status = "missing"
        elif sha256_file(p) != a["sha256"]:
            status = "altered"
        else:
            status = "ok"
        if status == "ok":
            report["ok"] += 1
        else:
            report[status].append(a["id"])
        a["integrity"], a["last_verified"] = status, report["checked_at"]
    if rows:
        _save(rows)
    report["integrity_pct"] = round(100 * report["ok"] / len(rows), 1) if rows else None
    return report


def summary() -> dict:
    rows = load()
    by = {k: sum(1 for r in rows if r.get("integrity") == k) for k in INTEGRITY_AR}
    return {"total": len(rows), "size": sum(r.get("size", 0) for r in rows), "integrity": by,
            "integrity_pct": round(100 * by["ok"] / len(rows), 1) if rows else None}


def backup(out_dir: Path | None = None) -> Path:
    """نسخة احتياطية كاملة على نمط BagIt المبسط: data/registry.jsonl والأصول، وبيان البصمات، وbag-info.txt."""
    out_dir = Path(out_dir) if out_dir else backups_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    out = out_dir / f"bahith-vault-{stamp}.zip"
    rows = load()
    manifest, total = [], 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        reg = registry_path()
        if reg.exists():
            z.write(reg, "data/registry.jsonl")
            manifest.append(f"{sha256_file(reg)}  data/registry.jsonl")
            total += reg.stat().st_size
        for a in rows:
            p = path_of(a)
            if p.exists():
                z.write(p, f"data/vault/{a['vault_path']}")
                manifest.append(f"{a['sha256']}  data/vault/{a['vault_path']}")
                total += p.stat().st_size
        z.writestr("bagit.txt", "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n")
        z.writestr("manifest-sha256.txt", "\n".join(manifest) + "\n")
        z.writestr("bag-info.txt", f"Source-Organization: Bahith - Research and Knowledge Development Institution\n"
                                   f"Bagging-Date: {dt.date.today().isoformat()}\n"
                                   f"Payload-Oxum: {total}.{len(manifest)}\nAsset-Count: {len(rows)}\n")
    audit.log("HUMAN-AUTHOR", "vault_backup", None, files_changed=[out.name], decision=f"نسخة احتياطية: {len(rows)} أصلاً")
    return out
