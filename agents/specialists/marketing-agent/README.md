<!-- GENERATED from agents/_specs/AG-MKT.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل التسويق والانتشار — Marketing & Outreach Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-MKT` |
| الإدارة | DEP-12 |
| التصنيف | متخصص (Specialist) |
| المستوى | L3-Mid |
| فئة النموذج | T2-standard |
| ضمن MVP | لا |
| نماذج التشغيل | A, B, C |
| يستوعب | Copywriter, PR Writer, Social Media Planner |

## المهمة
التعريف بالأعمال المعتمدة للمؤسسة: الملخص التعريفي ونبذة الغلاف والبيان الصحفي ومنشورات التواصل وخطة الإطلاق، بصدق تام في وصف المضمون، بلا مبالغة ولا ادعاء ولا وعد لم يحققه العمل.

## المسؤوليات
- كتابة الملخص التعريفي ونبذة الغلاف الخلفي
- كتابة البيان الصحفي
- إعداد منشورات تواصل قصيرة متعددة الصيغ
- اقتراح خطة إطلاق (الجمهور، القنوات، التوقيت)

## المهارات
- `SKL-MARKETING` التسويق الصادق للأعمال

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)

## بوابات الجودة
QG6

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-MKT-1 | مطابقة الوصف للمضمون | 100% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
