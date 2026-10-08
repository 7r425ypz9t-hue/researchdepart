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
import threading
from pathlib import Path

from .base import AdapterUnavailable, Completion, ModelAdapter

TIMEOUT_S = int(os.environ.get("RKPOS_CLAUDE_TIMEOUT", "1800"))
TOOL_MARK = '<invoke name="'      # علامة استدعاء أداة يكتبه النموذج نصاً حين يظن أن لديه أدوات


def _known_locations() -> list[Path]:
    """مواضع التثبيت المعروفة حين لا تكون الأداة في PATH (يضعها المثبّت الرسمي ولا يضيفها أحياناً)."""
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    return [home / ".local/bin/claude.exe", home / ".local/bin/claude", appdata / "npm/claude.cmd",
            home / ".claude/local/claude", home / ".claude/local/claude.exe", Path("/opt/homebrew/bin/claude"),
            Path("/usr/local/bin/claude")]


def executable() -> str | None:
    found = os.environ.get("RKPOS_CLAUDE_BIN") or shutil.which("claude")
    if found:
        return found
    return next((str(p) for p in _known_locations() if p.is_file()), None)


def login_command() -> str | None:
    """أمر تسجيل الدخول بالمسار الكامل، صالح للصق في PowerShell أو الطرفية."""
    exe = executable()
    if not exe:
        return None
    import sys
    return f'& "{exe}" auth login' if sys.platform.startswith("win") else f'"{exe}" auth login'


NOT_LOGGED_IN = ("Claude Code غير مسجّل الدخول بحسابكم. من اللوحة: الإعدادات ← «تسجيل الدخول إلى Claude»؛ "
                 "أو انسخوا أمر الدخول بمساره الكامل من الإعدادات إلى PowerShell — ثم أعيدوا المحاولة.")


def add_to_user_path() -> str:
    """ويندوز: يضيف مجلد Claude Code إلى PATH الخاص بالمستخدم (لا يحتاج صلاحيات المسؤول)،
    فيعمل الأمر claude في كل نافذة PowerShell جديدة."""
    import sys
    if not sys.platform.startswith("win"):
        raise AdapterUnavailable("هذا الإجراء لويندوز وحده")
    exe = executable()
    if not exe:
        raise AdapterUnavailable("Claude Code غير مثبت")
    import ctypes
    import winreg  # type: ignore[import-not-found]
    folder = str(Path(exe).parent)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
        try:
            cur, kind = winreg.QueryValueEx(k, "Path")
        except FileNotFoundError:
            cur, kind = "", winreg.REG_EXPAND_SZ
        parts = [x for x in cur.split(";") if x]
        if folder.lower() not in (x.lower().rstrip("\\") for x in parts):
            winreg.SetValueEx(k, "Path", 0, kind, ";".join(parts + [folder]))
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "Environment", 0x2, 5000, None)  # WM_SETTINGCHANGE
    return folder


def auth_status() -> dict | None:
    """حالة تسجيل الدخول كما تبلغ بها الأداة (`claude auth status --json`)؛ None إن تعذّر السؤال."""
    exe = executable()
    if not exe:
        return None
    try:
        from .. import live
        r = subprocess.run([exe, "auth", "status", "--json"], capture_output=True, timeout=20, **live.hidden())
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

    def command(self, system_file: Path, stream: bool = True) -> list[str]:
        fmt = ["--output-format", "stream-json", "--verbose", "--include-partial-messages"] if stream else ["--output-format", "json"]
        return [executable(), "-p", *fmt, "--tools", "", "--no-session-persistence",
                "--model", self.model, "--system-prompt-file", str(system_file)]

    def _run(self, cmd: list[str], user: str, cwd: str) -> tuple[int, str, str, dict | None]:
        """يشغّل الأداة في الخلفية (بلا نافذة)، ويبث النص إلى القناة الحيّة أولاً بأول، ويقبل الإيقاف الفوري."""
        from .. import live
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                                **live.hidden())
        live.register(proc)
        err_buf: list[bytes] = []
        t_err = threading.Thread(target=lambda: err_buf.append(proc.stderr.read()), daemon=True)
        t_err.start()
        timer = threading.Timer(TIMEOUT_S, proc.kill)
        timer.start()
        result, lines, streamed, hallucinated = None, [], [], [False]
        try:
            proc.stdin.write(user.encode("utf-8"))
            proc.stdin.close()
            for raw in proc.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                lines.append(line)
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") == "stream_event":
                    ev = d.get("event") or {}
                    delta = ev.get("delta") or {}
                    if ev.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
                        t = delta.get("text", "")
                        live.append(t)
                        streamed.append(t)
                        if TOOL_MARK in "".join(streamed[-60:]):   # يكتب استدعاء أداة وهمياً: أوقفه فوراً
                            proc.kill()
                            hallucinated[0] = True
                            break
                elif d.get("type") == "result" or "result" in d and "is_error" in d:
                    result = d
            proc.wait()
        finally:
            timer.cancel()
            killed = live.unregister()
        t_err.join(timeout=5)
        if hallucinated[0]:
            raise AdapterUnavailable("حاول الوكيل استدعاء أدوات غير متاحة في وضع النص؛ أُوقف وتُعاد المحاولة")
        if killed:
            raise live.Interrupted("أوقف المؤلف الكتابة")
        return proc.returncode, "\n".join(lines[-5:]), b"".join(err_buf).decode("utf-8", errors="replace"), result

    def complete(self, system, user, max_tokens=16000, effort=None) -> Completion:
        if not self.available():
            raise AdapterUnavailable("Claude Code غير مثبت")
        with tempfile.TemporaryDirectory(prefix="rkpos-cc-") as tmp:
            sf = Path(tmp) / "system.md"
            sf.write_text(system, encoding="utf-8")
            code, out, err, d = self._run(self.command(sf, stream=True), user, tmp)
            if d is None and ("unknown option" in err.lower() or "include-partial" in err.lower()):
                code, out, err, d = self._run(self.command(sf, stream=False), user, tmp)   # إصدار قديم لا يبث
        d = d or {}
        if code != 0 and not d:
            if "not logged in" in (err + out).lower() or "/login" in (err + out):
                raise AdapterUnavailable(NOT_LOGGED_IN)
            raise AdapterUnavailable(f"claude exited {code}: {(err or out)[-500:]}")
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
