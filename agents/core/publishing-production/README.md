<!-- GENERATED from agents/_specs/AG-PUB.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل النشر والإنتاج — Publishing Production Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-PUB` |
| الإدارة | DEP-08 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L3-Professional |
| فئة النموذج | T2-standard |
| ضمن MVP | نعم |
| نماذج التشغيل | A, B, C |
| يستوعب | Manuscript Manager, Indexing Agent, Bibliography Agent (الإخراج), Layout Agent, EPUB Agent, PDF Production Agent, Prepress Agent, Cover Design Coordinator |

## المهمة
تحويل النسخة المعتمدة حرفياً إلى حزمة نشر احترافية: مخطوط مجمّع، وفهارس، وببليوغرافيا منسقة، وإخراج PDF وEPUB عربي سليم، وبيانات وصفية، وتنسيق الغلاف مع المصمم البشري.

## المسؤوليات
- تجميع المخطوط من الفصول المعتمدة وحساب checksum
- توليد الببليوغرافيا من Zotero/CSL بالأسلوب المعتمد
- بناء الفهارس (أعلام، أماكن، مفاهيم) والمحتويات
- الإخراج عبر Pandoc + XeLaTeX/LuaLaTeX (PDF) وEPUB3 RTL
- إعداد ملف البيانات الوصفية وبطاقة الغلاف للمصمم
- إزالة وسوم الادعاءات من نسخة الإخراج فقط بعد QG4

## المهارات
- `SKL-PDF` إنتاج PDF عربي
- `SKL-EPUB` إنتاج EPUB
- `SKL-INDEX` بناء الفهارس
- `SKL-APA` التنسيق وفق APA 7
- `SKL-BIBCLEAN` تنظيف الببليوغرافيا
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-PANDOC` Publishing Engine (Pandoc + XeLaTeX/LuaLaTeX) — needs_install
- `TL-CSL` Citation Processor (CSL / citeproc) — needs_install (pandoc --citeproc)
- `TL-EPUBCHECK` EPUBCheck — needs_install (Java)
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-GITHUB` GitHub — platform
- `TL-ZOTERO` Zotero Web API — needs_account

## بوابات الجودة
QG6

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-PUB-1 | زمن البناء من الاعتماد إلى الحزمة | < 1 يوم عمل |
| K-PUB-2 | أخطاء إخراج بعد QG6 | 0 حرجة |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
