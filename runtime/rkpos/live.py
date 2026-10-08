"""القناة الحيّة: ما يكتبه الوكيل الآن، حرفاً بحرف، لكل مشروع — مع إيقاف فوري عند الطوارئ.

- projects/<PID>/live/current.md: النص الجاري (يُفرَّغ عند بدء خطوة جديدة؛ المخرجات النهائية محفوظة في runs/).
- projects/<PID>/live/current.json: من يكتب، وأي خطوة، ومنذ متى، وهل ما زال يكتب، ورقم الجلسة.
- stop_now(pid): يقتل عملية الكتابة الجارية فوراً، فيرفع المحوّل Interrupted ويتوقف الطيار بسؤال.
"""
from __future__ import annotations
import json
import subprocess
import sys
import threading

from .ids import now_iso
from .paths import PROJECTS

_local = threading.local()
_PROCS: dict[str, subprocess.Popen] = {}
_KILLED: set[str] = set()
_LOCK = threading.Lock()
NO_WINDOW = 0x08000000 if sys.platform.startswith("win") else 0   # CREATE_NO_WINDOW: لا نافذة سوداء في ويندوز


def hidden() -> dict:
    """وسائط subprocess لتشغيل أداة في الخلفية دون إظهار نافذة (ويندوز): بلا نافذة طرفية،
    ومع أمر إخفاء صريح لأي نافذة تحاول الأداة إظهارها (يشمل الطرفية الافتراضية Windows Terminal)."""
    if not NO_WINDOW:
        return {}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return {"creationflags": NO_WINDOW, "startupinfo": si}


class Interrupted(RuntimeError):
    """أوقف المؤلف الكتابة إيقافاً فورياً."""


def _dir(pid):
    d = PROJECTS / pid / "live"
    d.mkdir(parents=True, exist_ok=True)
    return d


def current() -> str | None:
    return getattr(_local, "pid", None)


def begin(pid: str | None, label: str, agent: str) -> None:
    _local.pid = pid
    _local.streamed = False
    if not pid or not (PROJECTS / pid).exists():
        return
    d = _dir(pid)
    old = json.loads((d / "current.json").read_text(encoding="utf-8")) if (d / "current.json").exists() else {}
    meta = {"seq": int(old.get("seq", 0)) + 1, "label": label, "agent": agent, "started": now_iso(), "running": True}
    (d / "current.md").write_text("", encoding="utf-8")
    (d / "current.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    with _LOCK:
        _KILLED.discard(pid)


def append(text: str, streamed: bool = True) -> None:
    pid = current()
    if streamed:
        _local.streamed = True
    if not pid or not text or not (PROJECTS / pid).exists():
        return
    with open(_dir(pid) / "current.md", "a", encoding="utf-8") as f:
        f.write(text)


def was_streamed() -> bool:
    return bool(getattr(_local, "streamed", False))


def end(ok: bool = True) -> None:
    pid = current()
    if pid and (PROJECTS / pid).exists():
        f = _dir(pid) / "current.json"
        meta = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        meta.update(running=False, ended=now_iso(), ok=ok)
        f.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    _local.pid = None


def register(proc: subprocess.Popen) -> None:
    pid = current()
    if pid:
        with _LOCK:
            _PROCS[pid] = proc


def unregister() -> bool:
    """يعيد True إن كانت العملية قد أُوقفت بطلب المؤلف."""
    pid = current()
    with _LOCK:
        _PROCS.pop(pid, None)
        return pid in _KILLED


def stop_now(pid: str) -> bool:
    with _LOCK:
        _KILLED.add(pid)
        proc = _PROCS.get(pid)
    if proc and proc.poll() is None:
        proc.kill()
        return True
    return False


def read(pid: str, offset: int = 0) -> dict:
    d = PROJECTS / pid / "live"
    meta = json.loads((d / "current.json").read_text(encoding="utf-8")) if (d / "current.json").exists() else {}
    text = (d / "current.md").read_text(encoding="utf-8") if (d / "current.md").exists() else ""
    return {"meta": meta, "offset": len(text), "text": text[offset:] if offset <= len(text) else text, "reset": offset > len(text)}
