# MEM-AUTHOR — ذاكرة المؤلف (AUTHOR_ONLY)

- **المحتوى** في `memory/author/private/` (غير متتبع في git؛ يفحص `scripts/security_scan.py` أنه لم يُتتبع خطأً):
  - `items.jsonl`: العناصر المعتمدة وفق `schemas/memory_item.schema.json`.
  - `candidates.jsonl`: المرشحات `AUTHOR_ONLY` قبل الاعتماد (لا تمر بـ `knowledge-base/candidates/` المتتبع).
- **سجل الاعتمادات** (معرّفات بلا محتوى): [APPROVALS.md](APPROVALS.md).
- الترقية إلى هذه الطبقة لا تتم إلا بـ `--approved-by HUMAN-AUTHOR` (L4)، والعنصر `AUTHOR_ONLY` لا يُرقّى إلى أي طبقة أخرى.
- **النسخ الاحتياطي:** لأن المحتوى خارج git، يُحفظ نسخة منه لدى المؤلف (جهازه أو خزنة مشفرة) — لا في مجلد Drive مشترك.
