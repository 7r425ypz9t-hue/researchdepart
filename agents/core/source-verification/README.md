<!-- GENERATED from agents/_specs/AG-SRC.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل التحقق من المصادر والمكتبة المرجعية — Source Verification Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SRC` |
| الإدارة | DEP-02 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L3-Professional |
| فئة النموذج | T2-standard |
| ضمن MVP | نعم |
| نماذج التشغيل | A, B, C |
| يستوعب | Research Librarian (الفهرسة), Bibliography Agent (قاعدة المراجع), DOI Verification |

## المهمة
أن يكون حارس بوابة سجل المصادر: لا يدخل مصدر إلى MEM-SOURCE إلا بعد التحقق من وجوده وبياناته الوصفية وDOI وحالة السحب، ومزامنته مع Zotero بوصفه المرجع الرئيس.

## المسؤوليات
- التحقق من DOI عبر Crossref والبيانات الوصفية عبر OpenAlex
- مطابقة العنوان والمؤلفين والسنة والناشر مع ما يرجعه المصدر الرسمي
- فحص حالة السحب/التصحيح (Crossref/Retraction Watch)
- تصنيف المصدر على الهرم وتحديد Peer_Reviewed وReliability_Level
- إنشاء/تحديث السجل وفق schemas/source.schema.json ومزامنته مع Zotero
- إزالة التكرار وتنظيف الببليوغرافيا

## المهارات
- `SKL-DOI` التحقق من DOI
- `SKL-CITEVERIFY` التحقق من الاستشهاد
- `SKL-META` استخلاص البيانات الوصفية
- `SKL-BIBCLEAN` تنظيف الببليوغرافيا

## الأدوات
- `TL-CROSSREF` Crossref REST API — public_api
- `TL-OPENALEX` OpenAlex API — public_api
- `TL-S2` Semantic Scholar API — public_api
- `TL-ZOTERO` Zotero Web API — needs_account
- `TL-PDFPARSE` PDF Parser — needs_install (pypdf / pdfplumber / GROBID)
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-SQL` SQL Database — built_in (SQLite) / needs_install (PostgreSQL)

## بوابات الجودة
QG1, QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SRC-1 | نسبة المصادر المتحقق منها | >= 95% من القابلة للتحقق |
| K-SRC-2 | Reference Error Rate | < 1% |
| K-SRC-3 | DOI مختلق | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
