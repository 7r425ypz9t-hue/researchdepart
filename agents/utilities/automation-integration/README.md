<!-- GENERATED from agents/_specs/AG-AUT.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الأتمتة والتكامل — Automation & Integration Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-AUT` |
| الإدارة | DEP-10 |
| التصنيف | خدمي (Utility) |
| المستوى | L3-Professional |
| فئة النموذج | T2-standard |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Automation Agent, RAG Engineer Agent (التشغيل), Metadata Agent (الآلي) |

## المهمة
تشغيل وصيانة خطوط الأتمتة والموصلات: مزامنة Zotero/Drive/GitHub، وخط استيعاب RAG، وفحوص CI، والجدولة — دون المساس بالمحتوى أو الصلاحيات.

## المسؤوليات
- صيانة GitHub Actions والسكربتات
- مزامنة الموصلات ومراقبة صحتها
- {'خط الاستيعاب': 'تقطيع، تضمين، فهرسة، تحديث البيانات الوصفية'}
- مراقبة الأعطال ورفع تذاكر

## المهارات
- `SKL-PIPELINE` تشغيل خطوط الأتمتة
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-GITHUB` GitHub — platform
- `TL-PY` Python Sandbox — built_in
- `TL-VDB` Vector Database — needs_install (pgvector/Qdrant/Chroma)
- `TL-ZOTERO` Zotero Web API — needs_account
- `TL-GDRIVE` Google Drive — platform
- `TL-FS` Repository File System — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-SQL` SQL Database — built_in (SQLite) / needs_install (PostgreSQL)

## بوابات الجودة
—

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-AUT-1 | نسبة الأتمتة في المهام الروتينية | >= 60% (Model B) |
| K-AUT-2 | توافر الموصلات | >= 99% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
