#!/usr/bin/env bash
# بناء PDF وEPUB عربي من النسخة المعتمدة (ST-APPROVED) — SKL-PDF / SKL-EPUB
# المتطلبات: pandoc, xelatex (texlive-xetex + texlive-lang-arabic), خط Noto Naskh Arabic, epubcheck (اختياري)
set -euo pipefail
PID="${1:?usage: build_publication.sh <PROJECT_ID>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/projects/$PID/manuscript/approved"
OUT="$ROOT/publishing/$PID"
mkdir -p "$OUT"
shopt -s nullglob
CHAPTERS=("$SRC"/*.md)
[ ${#CHAPTERS[@]} -gt 0 ] || { echo "no approved chapters in $SRC (QG5 + L4 approval required)"; exit 2; }
# checksum النسخة المعتمدة — يطابقه مشرف النشر في QG6
cat "${CHAPTERS[@]}" | sha256sum | cut -d' ' -f1 > "$OUT/approved.sha256"
# إزالة وسوم الادعاءات من نسخة الإخراج فقط (لا تمس المصدر)
TMP="$(mktemp -d)"
for f in "${CHAPTERS[@]}"; do
  sed -E 's/\[(FACT|EBI|INTERP|HYP|AUTHOR)\] ?//g' "$f" > "$TMP/$(basename "$f")"
done
BIB="$ROOT/projects/$PID/research/references.json"
CSL="${CSL:-$ROOT/publishing/csl/apa.csl}"
CITE_ARGS=()
[ -f "$BIB" ] && CITE_ARGS+=(--citeproc --bibliography "$BIB")
[ -f "$CSL" ] && CITE_ARGS+=(--csl "$CSL")
META="$ROOT/projects/$PID/publishing_profile.yaml"
META_ARGS=()
[ -f "$META" ] && META_ARGS+=(--metadata-file "$META")
pandoc "$TMP"/*.md "${CITE_ARGS[@]}" "${META_ARGS[@]}" \
  --pdf-engine=xelatex --template="$ROOT/publishing/templates/arabic-book.latex" \
  -V dir=rtl -V lang=ar -V mainfont="Noto Naskh Arabic" --toc -o "$OUT/book.pdf" 2> "$OUT/build_log.txt"
pandoc "$TMP"/*.md "${CITE_ARGS[@]}" "${META_ARGS[@]}" -V dir=rtl -V lang=ar \
  --css="$ROOT/publishing/templates/epub-rtl.css" --toc -o "$OUT/book.epub" 2>> "$OUT/build_log.txt"
if command -v epubcheck >/dev/null; then epubcheck "$OUT/book.epub" > "$OUT/epubcheck.txt" 2>&1 || echo "EPUBCheck reported issues"; fi
echo "built → $OUT"
