<!-- GENERATED from agents/_specs/AG-WCH.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الرصد البحثي المستمر — Research Watch Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-WCH` |
| الإدارة | DEP-02 |
| التصنيف | خدمي (Utility) |
| المستوى | L2-Associate |
| فئة النموذج | T1-economy |
| ضمن MVP | لا |
| نماذج التشغيل | C |
| يستوعب | — |

## المهمة
رصد مستمر لموضوعات المشاريع النشطة: تسجيل الدراسات الجديدة المهمة، والتحقق منها، وتصنيفها، وربطها بالمشروع، وإرسال توصية — دون أي تعديل تلقائي للمخطوط.

## المسؤوليات
- تشغيل استعلامات مجدولة (OpenAlex/Crossref/S2) لكل مشروع نشط
- فرز النتائج الجديدة وتقدير الأهمية
- إحالة المرشحات المهمة إلى AG-SRC للتحقق
- إصدار Watch Recommendation مرتبط بفصل/ادعاء

## المهارات
- `SKL-LITSEARCH` البحث في الأدبيات
- `SKL-META` استخلاص البيانات الوصفية

## الأدوات
- `TL-OPENALEX` OpenAlex API — public_api
- `TL-CROSSREF` Crossref REST API — public_api
- `TL-S2` Semantic Scholar API — public_api
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in

## بوابات الجودة
—

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-WCH-1 | نسبة التوصيات ذات الصلة (حكم المؤلف) | >= 60% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
