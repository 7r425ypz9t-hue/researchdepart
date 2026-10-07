<!-- GENERATED from agents/_specs/AG-SUP-PUB.yaml by `rkpos generate` — do not edit by hand. -->
# مشرف النشر — Publishing Supervisor

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SUP-PUB` |
| الإدارة | DEP-11 |
| التصنيف | إشرافي (Supervisory) |
| المستوى | L4-Senior |
| فئة النموذج | T2-standard |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
الحكم على جاهزية ملفات النشر (QG6) والأرشفة (QG7): سلامة الإخراج والخطوط والفهارس والبيانات الوصفية والمعرّفات، ومطابقة النسخة المنشورة للنسخة المعتمدة حرفياً.

## المسؤوليات
- مطابقة checksum النسخة المعتمدة مع مصدر الإخراج
- فحص PDF/EPUB (الخطوط المضمّنة، الاتجاه RTL، الروابط، الفهرس)
- فحص البيانات الوصفية (ISBN إن وُجد، العنوان، المؤلف، الحقوق)
- إصدار قرار QG6 ومراجعة اكتمال الأرشيف QG7

## المهارات
- `SKL-PDF` إنتاج PDF عربي
- `SKL-EPUB` إنتاج EPUB
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-EPUBCHECK` EPUBCheck — needs_install (Java)
- `TL-PDFPARSE` PDF Parser — needs_install (pypdf / pdfplumber / GROBID)
- `TL-GITHUB` GitHub — platform

## بوابات الجودة
QG6, QG7

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SPB-1 | أخطاء إخراج بعد الإصدار | 0 حرجة |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
