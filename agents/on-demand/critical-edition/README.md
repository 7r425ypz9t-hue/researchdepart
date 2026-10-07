<!-- GENERATED from agents/_specs/AG-TAH.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل تحقيق المخطوطات — Critical Edition (Tahqiq) Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-TAH` |
| الإدارة | DEP-02 |
| التصنيف | عند الطلب (On-Demand) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | C |
| يستوعب | — |

## المهمة
مساعدة المحقق البشري في تحقيق النصوص التراثية: التفريغ عبر OCR والتحقق منه، ومقابلة النسخ، ورصد الفروق، وتخريج النصوص، وبناء الجهاز النقدي — مع بقاء الترجيح للمحقق.

## المسؤوليات
- تفريغ صور المخطوط (OCR عربي) وقياس دقته
- المقابلة بين النسخ ورصد الفروق في جدول
- اقتراح التخريجات (الآيات، الأحاديث، الأشعار، الأعلام) للتحقق البشري
- بناء الجهاز النقدي والحواشي

## المهارات
- `SKL-OCRVAL` التحقق من التفريغ الضوئي
- `SKL-COLLATION` مقابلة النسخ
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-OCR` Arabic OCR — needs_install (Tesseract ara) / needs_account (خدمات سحابية)
- `TL-PY` Python Sandbox — built_in
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in

## بوابات الجودة
QG1, QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-TAH-1 | دقة التفريغ على العينة المرجعية | >= 98% بعد المراجعة |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
