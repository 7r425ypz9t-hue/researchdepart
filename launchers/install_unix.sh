#!/bin/bash
# «باحث» — مثبّت ماك ولينكس بسطر واحد: ينزّل البرنامج أو يحدّثه دون مساس بمشاريعكم وذاكرتكم، ويثبّت الحزمة،
# ويستعيد الذاكرة الخاصة إن وُجدت نسختها الاحتياطية، وينشئ الأيقونة، ويفتح اللوحة ويتحقق أنها قامت.
# من الإنترنت (في الطرفية):
#   curl -fsSL https://raw.githubusercontent.com/7r425ypz9t-hue/researchdepart/refs/heads/claude/clever-carson-78yimu/launchers/install_unix.sh | bash
# الخيارات (متغيرات بيئة): BAHITH_SOURCE نسخة محلية بدل التنزيل · BAHITH_ROOT مجلد التثبيت · BAHITH_REF الفرع
#                         BAHITH_NO_LAUNCH=1 للاختبار (بلا pip ولا أيقونة ولا تشغيل)
set -euo pipefail
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
REPO="https://github.com/7r425ypz9t-hue/researchdepart"
REF="${BAHITH_REF:-claude/clever-carson-78yimu}"
SOURCE="${BAHITH_SOURCE:-${1:-}}"
RK="$HOME/.rkpos"
say() { printf '  » %s\n' "$1"; }
fail() { printf '  ✖ %s\n' "$1" >&2; exit 1; }
is_bahith() { [ -n "${1:-}" ] && [ -f "$1/runtime/rkpos/__main__.py" ]; }

echo; echo "  باحث — مؤسسة البحث والتطوير المعرفي"; echo "  التثبيت والتحديث على هذا الجهاز"; echo

say "التحقق من Python…"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PY="$(command -v "$c")"; break
  fi
done
if [ -z "$PY" ]; then
  [ "$(uname)" = "Darwin" ] && open "https://www.python.org/downloads/macos/"
  fail "يلزم Python 3.10 أو أحدث. ثبّتوه من python.org ثم أعيدوا تشغيل المثبّت."
fi
say "Python: $PY"

# مجلد البرنامج: التثبيت القائم أولاً (السجل، ثم آخر تشغيل للوحة)، كي تبقى المشاريع في مكانها
find_root() {
  local f r
  for f in "$RK/install.json" "$RK/panel.json"; do
    r="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1],encoding="utf-8")).get("root",""))' "$f" 2>/dev/null || true)"
    if is_bahith "$r"; then echo "$r"; return; fi
  done
  local docs="$HOME/Documents"; [ -d "$docs" ] || docs="$HOME"
  for r in "$docs/researchdepart-main" "$docs/researchdepart"; do is_bahith "$r" && { echo "$r"; return; }; done
  echo "$docs/Bahith"
}
ROOT="${BAHITH_ROOT:-$(find_root)}"
ROOT="$(cd "$(dirname "$ROOT")" 2>/dev/null && pwd || dirname "$ROOT")/$(basename "$ROOT")"
PARENT="$(dirname "$ROOT")"; mkdir -p "$PARENT"
say "مجلد البرنامج: $ROOT"

stop_bahith() { pkill -f -- "-m rkpos panel" >/dev/null 2>&1 || true; sleep 0.5; }

copy_user_data() {   # ينقل ما في user-data.txt (من الإصدار الجديد) من التثبيت السابق؛ ما للمؤلف يغلب ما في الإصدار
  local old="$1" new="$2" list="$2/launchers/user-data.txt" n=0 p item rel
  [ -f "$list" ] || fail "قائمة بيانات المؤلف مفقودة من الإصدار الجديد؛ أُوقف التحديث حفاظاً على بياناتكم."
  shopt -s nullglob dotglob
  while IFS= read -r p || [ -n "$p" ]; do
    p="${p%%$'\r'}"; [ -z "$p" ] && continue; [ "${p:0:1}" = "#" ] && continue
    for item in "$old"/$p; do
      [ -e "$item" ] || continue
      rel="${item#"$old"/}"
      mkdir -p "$(dirname "$new/$rel")"; rm -rf "${new:?}/$rel"; cp -a "$item" "$new/$rel"; n=$((n+1))
    done
  done < "$list"
  shopt -u nullglob dotglob
  say "نُقل $n عنصراً من بيانات المؤلف."
}

if [ -d "$ROOT/.git" ]; then
  command -v git >/dev/null || fail "المجلد نسخة git ولا يوجد git. حدّثوه بأنفسكم ثم أعيدوا التشغيل."
  say "تحديث نسخة git…"; stop_bahith
  git -C "$ROOT" pull --ff-only || fail "تعذّر تحديث نسخة git (تعديلات محلية أو فرع متباعد). لم يُمسّ شيء."
else
  STAGE="$(mktemp -d "$PARENT/bahith-staging.XXXXXX")"
  trap 'rm -rf "$STAGE"' EXIT
  if [ -n "$SOURCE" ]; then
    say "نسخ البرنامج من المجلد المحلي…"
    mkdir -p "$STAGE/app"; (cd "$SOURCE" && tar --exclude=.git -cf - .) | (cd "$STAGE/app" && tar -xf -)
    NEW="$STAGE/app"
  else
    say "تنزيل البرنامج…"
    OK=0
    for r in "$REF" main; do curl -fsSL "$REPO/archive/refs/heads/$r.zip" -o "$STAGE/bahith.zip" && { OK=1; break; }; done
    [ "$OK" = 1 ] || fail "تعذّر التنزيل. تحققوا من الاتصال ثم أعيدوا التشغيل."
    (cd "$STAGE" && unzip -q bahith.zip && rm bahith.zip)
    NEW="$(find "$STAGE" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  fi
  is_bahith "$NEW" || fail "ملفات البرنامج ناقصة."
  if is_bahith "$ROOT"; then
    say "نقل مشاريعكم وذاكرتكم وسجلاتكم إلى الإصدار الجديد…"
    stop_bahith
    copy_user_data "$ROOT" "$NEW"
    rm -rf "$ROOT.previous"; mv "$ROOT" "$ROOT.previous"   # النسخة السابقة كاملة احتياطاً حتى التثبيت التالي
  elif [ -e "$ROOT" ]; then
    fail "المجلد $ROOT موجود وليس فيه «باحث». اختاروا مجلداً آخر بالمتغير BAHITH_ROOT."
  fi
  mv "$NEW" "$ROOT"
fi

mkdir -p "$RK"
"$PY" -c 'import json,sys,datetime;json.dump({"root":sys.argv[1],"ref":sys.argv[2],"installed_at":datetime.datetime.now().isoformat(timespec="seconds")},open(sys.argv[3],"w",encoding="utf-8"),ensure_ascii=False)' "$ROOT" "$REF" "$RK/install.json"
if [ "${BAHITH_NO_LAUNCH:-}" = 1 ]; then say "تم (وضع الاختبار)."; exit 0; fi

cd "$ROOT"
say "تثبيت الحزمة ومتطلباتها…"
"$PY" -m pip install --user --quiet --disable-pip-version-check -e . pillow >/dev/null 2>&1 || \
  "$PY" -m pip install --user --quiet --disable-pip-version-check --break-system-packages -e . pillow || \
  fail "تعذّر تثبيت الحزمة (pip)."

if [ ! -d "$ROOT/memory/author/private" ]; then
  for b in "$ROOT/midad-private-backup.tar.gz" "$HOME/Downloads/midad-private-backup.tar.gz"; do
    if [ -f "$b" ]; then say "استعادة الذاكرة الخاصة…"; tar -xzf "$b" -C "$ROOT"; break; fi
  done
fi

say "إنشاء الأيقونة على سطح المكتب…"
"$PY" -m rkpos install-icon >/dev/null || fail "تعذّر إنشاء الأيقونة."
[ -f "$RK/fonts/adwa-assalaf.ttf" ] && "$PY" -m rkpos fonts system >/dev/null 2>&1 || true

say "فتح لوحة التحكم…"
stop_bahith; rm -f "$RK/panel.json"
nohup "$PY" -m rkpos panel >>"$RK/panel.log" 2>&1 &
UP=0
for _ in $(seq 1 40); do sleep 0.5
  PORT="$("$PY" -c 'import json,os;print(json.load(open(os.path.expanduser("~/.rkpos/panel.json")))["port"])' 2>/dev/null || true)"
  [ -n "$PORT" ] && curl -fs "http://127.0.0.1:$PORT/" >/dev/null 2>&1 && { UP=1; break; }
done
if [ "$UP" != 1 ]; then
  echo; echo "  ✖ لم تبدأ اللوحة. هذا ما أعاده التشغيل — أرسلوه كما هو:"
  "$PY" -c "import rkpos.panel.server; print('rkpos.panel: OK')" || true
  tail -n 20 "$RK/panel.log" 2>/dev/null || true
  exit 1
fi
echo; echo "  ✔ اكتمل التثبيت، واللوحة تعمل. من الآن: انقروا أيقونة «باحث» على سطح المكتب."
echo "  البرنامج ومشاريعكم: $ROOT"
[ -d "$ROOT.previous" ] && echo "  النسخة السابقة محفوظة احتياطاً في: $ROOT.previous"
echo
