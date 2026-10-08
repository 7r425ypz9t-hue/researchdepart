"""Claude Code adapter — يشغّل الوكيل عبر أداة Claude Code المثبّتة على جهاز المؤلف (`claude -p`).

يستعمل حساب Claude المسجَّل في الأداة نفسها (اشتراك أو مفتاح)، فلا يحتاج المستودع إلى مفتاح API.
- البرومبت النظامي يُمرَّر في ملف مؤقت (`--system-prompt-file`) والمهمة عبر stdin؛
  فلا يمر نص عربي طويل في سطر الأوامر (حدود الطول ومحارف cmd في ويندوز).
- `--tools ""`: الوكيل يكتب نصاً فقط، لا يقرأ ملفات ولا ينفذ أوامر (Least Privilege).
- يُشغَّل من مجلد مؤقت فارغ حتى لا تُحقن ملفات CLAUDE.md من المستودع في السياق.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import AdapterUnavailable, Completion, ModelAdapter

TIMEOUT_S = int(os.environ.get("RKPOS_CLAUDE_TIMEOUT", "1800"))


def executable() -> str | None:
    return os.environ.get("RKPOS_CLAUDE_BIN") or shutil.which("claude")


NOT_LOGGED_IN = ("Claude Code غير مسجّل الدخول بحسابكم. من اللوحة: الإعدادات ← «تسجيل الدخول إلى Claude»؛ "
                 "أو في PowerShell: claude auth login — ثم أعيدوا المحاولة.")


def auth_status() -> dict | None:
    """حالة تسجيل الدخول كما تبلغ بها الأداة (`claude auth status --json`)؛ None إن تعذّر السؤال."""
    exe = executable()
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "auth", "status", "--json"], capture_output=True, timeout=20)
        return json.loads(r.stdout.decode("utf-8", errors="replace") or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def open_login_window() -> str:
    """يفتح نافذة طرفية مرئية تشغّل `claude auth login` (يفتح المتصفح لتسجيل الدخول بالاشتراك)."""
    import sys
    exe = executable()
    if not exe:
        raise AdapterUnavailable("Claude Code غير مثبت")
    if sys.platform.startswith("win"):
        subprocess.Popen([exe, "auth", "login"], creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0x10))
    elif sys.platform == "darwin":
        q = exe.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "\\"{q}\\" auth login"',
                          "-e", 'tell application "Terminal" to activate'])
    else:
        term = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal") or shutil.which("xterm")
        if not term:
            raise AdapterUnavailable("لا طرفية رسومية؛ نفّذوا: claude auth login")
        subprocess.Popen([term, "-e", exe, "auth", "login"])
    return exe


class ClaudeCodeAdapter(ModelAdapter):
    provider = "claude_code"

    def available(self) -> bool:
        return executable() is not None

    def command(self, system_file: Path) -> list[str]:
        return [executable(), "-p", "--output-format", "json", "--tools", "", "--no-session-persistence",
                "--model", self.model, "--system-prompt-file", str(system_file)]

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        if not self.available():
            raise AdapterUnavailable("Claude Code غير مثبت (npm install -g @anthropic-ai/claude-code)")
        with tempfile.TemporaryDirectory(prefix="rkpos-cc-") as tmp:
            sf = Path(tmp) / "system.md"
            sf.write_text(system, encoding="utf-8")
            r = subprocess.run(self.command(sf), input=user.encode("utf-8"), capture_output=True, cwd=tmp,
                               timeout=TIMEOUT_S)
        out = r.stdout.decode("utf-8", errors="replace").strip()
        try:
            d = json.loads(out.splitlines()[-1] if out else "{}")
        except json.JSONDecodeError:
            d = {}
        if r.returncode != 0 and not d:
            err = r.stderr.decode("utf-8", errors="replace").strip()[-500:]
            if "not logged in" in (err + out).lower() or "/login" in (err + out):
                raise AdapterUnavailable(NOT_LOGGED_IN)
            raise AdapterUnavailable(f"claude exited {r.returncode}: {err or out[-500:]}")
        if d.get("is_error"):
            msg = str(d.get("result"))
            if "not logged in" in msg.lower() or "/login" in msg:
                raise AdapterUnavailable(NOT_LOGGED_IN)
            raise AdapterUnavailable(f"claude error: {msg[:500]}")
        u = d.get("usage") or {}
        tin = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        served = next(iter(d.get("modelUsage") or {}), self.model)
        refused = d.get("stop_reason") == "refusal"
        return Completion(text="" if refused else (d.get("result") or ""), model=f"claude_code:{served}",
                          input_tokens=tin, output_tokens=int(u.get("output_tokens") or 0),
                          stop_reason=d.get("stop_reason"), refused=refused,
                          raw={"total_cost_usd": d.get("total_cost_usd"), "duration_ms": d.get("duration_ms")})
