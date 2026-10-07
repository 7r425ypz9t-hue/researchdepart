<!-- GENERATED from agents/_specs/AG-TRN.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل الترجمة والمواءمة المصطلحية — Translation Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-TRN` |
| الإدارة | DEP-05 |
| التصنيف | عند الطلب (On-Demand) |
| المستوى | L3-Professional |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
نقل النصوص بين العربية والإنجليزية (وغيرهما عند الإمكان) نقلاً أميناً للمعنى والمصطلح والسجل، مع ذاكرة ترجمة ومسرد ثنائي، وتمييز الترجمة الحرفية للاقتباس عن الترجمة الحرة.

## المسؤوليات
- الترجمة وفق المسرد الثنائي وذاكرة الترجمة
- وسم مواضع الالتباس وخيارات النقل
- ترجمة الاقتباسات مع الإحالة إلى الأصل ووسم (ترجمة المؤلف)

## المهارات
- `SKL-TRANSLATE` الترجمة المصطلحية
- `SKL-TERMS` إدارة المصطلحات

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)

## بوابات الجودة
QG4, QG5

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-TRN-1 | أخطاء معنى في المطابقة العيّنية | 0 حرجة |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
