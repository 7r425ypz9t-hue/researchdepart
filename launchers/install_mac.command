#!/bin/bash
# ===== تثبيت لوحة «باحث» على ماك =====
# المتطلبات: Python 3.10+ (python.org أو Homebrew) — واختيارياً Claude Code للتشغيل الآلي.
cd "$(dirname "$0")/.." || exit 1
PY=python3
echo "[1/3] تثبيت الحزمة..."
"$PY" -m pip install --user -e . || { echo "تعذّر التثبيت"; read -r; exit 1; }
echo "[2/3] استعادة الذاكرة الخاصة إن وُجدت النسخة الاحتياطية..."
for f in "midad-private-backup.tar.gz" "$HOME/Downloads/midad-private-backup.tar.gz"; do
  if [ -f "$f" ]; then tar -xzf "$f" && echo "    تمت الاستعادة من $f"; break; fi
done
echo "[3/3] إنشاء الأيقونة على سطح المكتب..."
"$PY" -m rkpos install-icon || { echo "تعذّر إنشاء الأيقونة"; read -r; exit 1; }
echo "تم. افتحوا أيقونة «باحث» من سطح المكتب (أو من مجلد التطبيقات)."
read -r -p "اضغط Enter للإغلاق"
