"""تثبيت أيقونة «مِداد» على سطح المكتب (ويندوز · ماك · لينكس).

يُشغَّل على جهاز المؤلف: `rkpos install-icon` (والإزالة: `rkpos install-icon --remove`).
الأيقونة تشغّل `rkpos panel` بمفسّر بايثون الحالي، وتحفظ مسار Claude Code ومسار البحث (PATH)
وقت التثبيت؛ لأن تطبيقات سطح المكتب في ماك ولينكس لا ترث PATH الطرفية فلا تجد الأمر claude.
"""
from __future__ import annotations
import os
import plistlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from ..paths import ROOT

STATIC = Path(__file__).parent / "static"
NAME_AR = "مداد"
HOME_DIR = Path.home() / ".rkpos"


def _desktop() -> Path:
    if sys.platform.startswith("win"):
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                                 capture_output=True, text=True, timeout=20).stdout.strip()
            if out:
                return Path(out)
        except (OSError, subprocess.SubprocessError):
            pass
    elif not sys.platform.startswith("darwin"):
        try:
            out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=5).stdout.strip()
            if out:
                return Path(out)
        except (OSError, subprocess.SubprocessError):
            pass
    return Path.home() / "Desktop"


def _python(gui: bool) -> str:
    exe = Path(sys.executable)
    if gui and sys.platform.startswith("win"):
        w = exe.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return str(exe)


def _env_lines() -> dict:
    """ما يحتاجه المشغّل ليجد Claude Code خارج الطرفية."""
    from ..adapters.claude_code_adapter import executable
    env = {"RKPOS_ROOT": str(ROOT), "PATH": os.environ.get("PATH", "")}
    if executable():
        env["RKPOS_CLAUDE_BIN"] = executable()
    return env


def _sh_launcher() -> Path:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    env = _env_lines()
    q = lambda s: "'" + s.replace("'", "'\\''") + "'"  # noqa: E731
    body = "#!/bin/sh\n# مشغّل لوحة «مِداد» — أنشأه rkpos install-icon\n"
    body += "".join(f"export {k}={q(v)}\n" for k, v in env.items())
    body += f"exec {q(_python(False))} -m rkpos panel >> {q(str(HOME_DIR / 'panel.log'))} 2>&1\n"
    p = HOME_DIR / "midad-launch.sh"
    p.write_text(body, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def shortcut_script(targets: list[Path], ico: Path) -> str:
    """نص PowerShell عادي (لا ترميز ولا تجاوز لسياسة التنفيذ) ينشئ اختصاراً يشير مباشرة إلى pythonw.
    لا ملفات وسيطة ولا تنزيل: ما تراه برامج الحماية هو ما يحدث فعلاً."""
    q = lambda x: str(x).replace("'", "''")  # noqa: E731
    parts = []
    for t in targets:
        parts.append(
            f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(t)}');"
            f"$s.TargetPath='{q(_python(True))}';$s.Arguments='-m rkpos panel';"
            f"$s.WorkingDirectory='{q(ROOT)}';$s.IconLocation='{q(ico)}';"
            "$s.Description='MIDAD control panel';$s.Save();")
    return "".join(parts)


def install_windows(remove: bool = False) -> list[str]:
    lnk = _desktop() / f"{NAME_AR}.lnk"
    start = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft/Windows/Start Menu/Programs" / f"{NAME_AR}.lnk"
    if remove:
        for p in (lnk, start):
            p.unlink(missing_ok=True)
        (HOME_DIR / "midad-launch.cmd").unlink(missing_ok=True)  # من إصدار سابق
        return [f"removed {lnk}", f"removed {start}"]
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    ico = HOME_DIR / "midad.ico"
    shutil.copyfile(STATIC / "midad.ico", ico)
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", shortcut_script([lnk, start], ico)], check=True)
    return [str(lnk), str(start)]


def install_macos(remove: bool = False) -> list[str]:
    app = Path.home() / "Applications" / "Midad.app"
    link = _desktop() / f"{NAME_AR}.app"
    if remove:
        if link.is_symlink() or link.exists():
            link.unlink()
        shutil.rmtree(app, ignore_errors=True)
        return [f"removed {app}", f"removed {link}"]
    launcher = _sh_launcher()
    macos = app / "Contents/MacOS"
    res = app / "Contents/Resources"
    macos.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STATIC / "midad.icns", res / "midad.icns")
    exe = macos / "midad"
    exe.write_text(f"#!/bin/sh\nexec '{launcher}'\n", encoding="utf-8")
    exe.chmod(0o755)
    with open(app / "Contents/Info.plist", "wb") as f:
        plistlib.dump({"CFBundleName": NAME_AR, "CFBundleDisplayName": NAME_AR, "CFBundleIdentifier": "org.midad.panel",
                       "CFBundleExecutable": "midad", "CFBundleIconFile": "midad.icns", "CFBundlePackageType": "APPL",
                       "CFBundleShortVersionString": "1.0", "LSUIElement": True}, f)
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(app)
    return [str(app), str(link)]


def install_linux(remove: bool = False) -> list[str]:
    apps = Path.home() / ".local/share/applications/midad.desktop"
    desk = _desktop() / "midad.desktop"
    if remove:
        for p in (apps, desk):
            p.unlink(missing_ok=True)
        return [f"removed {apps}", f"removed {desk}"]
    launcher = _sh_launcher()
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    icon = HOME_DIR / "midad.png"
    shutil.copyfile(STATIC / "midad.png", icon)
    entry = (f"[Desktop Entry]\nType=Application\nName={NAME_AR}\nName[ar]={NAME_AR}\n"
             f"Comment=لوحة تحكم إدارة البحوث والدراسات والنشر\nExec={launcher}\nIcon={icon}\nTerminal=false\n"
             "Categories=Office;Education;\n")
    out = []
    for p in (apps, desk):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entry, encoding="utf-8")
        p.chmod(0o755)
        out.append(str(p))
    try:  # GNOME: السماح بتشغيل الأيقونة من سطح المكتب
        subprocess.run(["gio", "set", str(desk), "metadata::trusted", "true"], capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass
    return out


def install(remove: bool = False) -> list[str]:
    if sys.platform.startswith("win"):
        return install_windows(remove)
    if sys.platform == "darwin":
        return install_macos(remove)
    return install_linux(remove)
