"""خط الهوية وأيقونة البرنامج — منقولان من «تراث»: الإيداع والرفض، والتثبيت في النظام، واعتماد الأيقونة، وتصدير Word."""
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from rkpos import appicon, fonts

REPO = Path(__file__).resolve().parents[1]
FAKE = b"\x00\x01\x00\x00" + b"\x00" * 2000 + "adwa-assalaf".encode("utf-16-be") + b"\x00" * 100


def _png(n: int) -> bytes:
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))  # noqa: E731
    raw = b"".join(b"\x00" + b"\x1f\x4e\x79\xff" * n for _ in range(n))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(fonts, "HOME_DIR", tmp_path / ".rkpos")
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def test_font_install_and_reject(home):
    assert fonts.install("adwa-assalaf_B.ttf", FAKE) == "bold"
    assert fonts.install("adwa-assalaf.ttf", FAKE) == "regular"
    assert fonts.status()["regular"] and fonts.status()["bold"]
    with pytest.raises(ValueError):
        fonts.install("x.ttf", b"PK\x03\x04" + b"\x00" * 3000)
    with pytest.raises(ValueError):
        fonts.install("other.ttf", b"\x00\x01\x00\x00" + b"\x00" * 3000)


@pytest.mark.skipif(sys.platform.startswith("win") or sys.platform == "darwin", reason="مجلد خطوط لينكس")
def test_font_into_operating_system(home):
    assert fonts.install_system() == []
    fonts.install("adwa-assalaf.ttf", FAKE)
    fonts.install("adwa-assalaf_B.ttf", FAKE)
    assert sorted(fonts.install_system()) == ["bold", "regular"]
    assert all(fonts.system_status().values()) and str(fonts.system_folder()).startswith(str(home))


def test_icon_adopt_and_reset(home):
    assert not appicon.custom() and appicon.paths()["ico"].name == "bahith.ico" and appicon.paths()["ico"].is_file()
    appicon.adopt(_png(512))
    assert appicon.custom()
    assert appicon.paths()["ico"].read_bytes()[:4] == b"\x00\x00\x01\x00"
    assert appicon.paths()["icns"].read_bytes()[:4] == b"icns"
    with pytest.raises(ValueError):
        appicon.adopt(b"not an image" * 20)
    appicon.reset()
    assert not appicon.custom()


def test_word_export_uses_identity_font_and_keeps_digits_whole(home):
    pytest.importorskip("docx")
    from rkpos import export
    fonts.install("adwa-assalaf.ttf", FAKE)
    data = export.to_docx("# عنوان\n\nصدر عام 1971 كتاب مهم.", title="عنوان")
    import io
    import zipfile
    xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8")
    assert 'w:cs="adwa-assalaf"' in xml
    assert '<w:t>1971</w:t>' in xml          # الأرقام في مقطع مستقل بخط Noto Naskh


def test_font_files_never_in_repository():
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.lower()
    assert not [ln for ln in out.splitlines() if ln.endswith((".ttf", ".otf", ".woff", ".woff2"))]
