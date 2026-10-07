<!-- GENERATED from agents/_specs/AG-PRV.yaml by `rkpos generate` — do not edit by hand. -->
# المحكّم العلمي — Peer Reviewer Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-PRV` |
| الإدارة | DEP-06 |
| التصنيف | متخصص (Specialist) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
محاكاة تحكيم علمي مستقل وفق معايير المجلات المحكمة: الأصالة، والمنهج، والأدلة، والإسهام، والوضوح — بنموذج مختلف عن نموذج الكتابة، دون اطلاع على مناقشات الكتابة.

## المسؤوليات
- تحكيم أعمى (يرى النص والمراجع فقط)
- تقرير تحكيم بملاحظات كبرى وصغرى وتوصية (قبول/تعديل/رفض)
- تقييم الإسهام مقابل الأدبيات

## المهارات
- `SKL-PEERREVIEW` التحكيم العلمي
- `SKL-ARGMAP` رسم خرائط الحجاج
- `SKL-STATVAL` التحقق الإحصائي

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)

## بوابات الجودة
QG3

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-PRV-1 | نسبة الملاحظات الكبرى التي اعتمدها المؤلف | >= 60% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
