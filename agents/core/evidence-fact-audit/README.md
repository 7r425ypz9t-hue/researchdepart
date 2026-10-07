<!-- GENERATED from agents/_specs/AG-EVA.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل تدقيق الأدلة والوقائع والاستشهادات — Evidence & Fact Audit Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-EVA` |
| الإدارة | DEP-07 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L3-Professional |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Fact Checker, Citation Auditor, Evidence Quality Agent, Statistics Auditor |

## المهمة
التدقيق المستقل لكل ادعاء في المسودة: هل المصدر موجود ومتحقق؟ هل يقول فعلاً ما نُسب إليه؟ هل الرقم صحيح وفي سياقه؟ هل الوسم مناسب؟ ثم إنتاج سجل تدقيق قابل للمراجعة.

## المسؤوليات
- استخراج الادعاءات من المسودة وربطها بسجل الأدلة
- مطابقة الادعاء مع نص المصدر (claim-source fidelity)
- التحقق من الأرقام والإحصاءات وإعادة حسابها عند الإمكان
- {'فحص الاستشهادات': 'الصيغة، الصفحة، السنة، وجود المرجع في القائمة'}
- فحص سلامة الوسم (FACT مقابل INTERP...)

## المهارات
- `SKL-FACTCHECK` تدقيق الوقائع
- `SKL-CITEVERIFY` التحقق من الاستشهاد
- `SKL-STATVAL` التحقق الإحصائي
- `SKL-CLAIMTAG` وسم الادعاءات
- `SKL-APA` التنسيق وفق APA 7

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-PDFPARSE` PDF Parser — needs_install (pypdf / pdfplumber / GROBID)
- `TL-PY` Python Sandbox — built_in
- `TL-CROSSREF` Crossref REST API — public_api
- `TL-ZOTERO` Zotero Web API — needs_account

## بوابات الجودة
QG1, QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-EVA-1 | Citation Accuracy | >= 99% |
| K-EVA-2 | Fact Error Rate بعد التدقيق | < 0.5% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
