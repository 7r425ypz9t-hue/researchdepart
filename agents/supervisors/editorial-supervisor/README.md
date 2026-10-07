<!-- GENERATED from agents/_specs/AG-SUP-EDT.yaml by `rkpos generate` — do not edit by hand. -->
# مشرف التحرير — Editorial Supervisor

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SUP-EDT` |
| الإدارة | DEP-11 |
| التصنيف | إشرافي (Supervisory) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
الحكم على جاهزية النص تحريرياً (QG5): البنية، والاتساق، والسجل اللغوي، والمصطلح، والوفاء بملاحظات التحكيم، دون إعادة كتابة النص.

## المسؤوليات
- التحقق من معالجة كل ملاحظات التحكيم والفريق الأحمر أو تعليل رفضها
- فحص الاتساق المصطلحي مع المسرد المعتمد
- فحص اتساق السجل مع بصمة المؤلف
- إصدار قرار QG5 والمشاركة في QG3

## المهارات
- `SKL-AREDIT` التحرير العربي الأكاديمي
- `SKL-TERMS` إدارة المصطلحات
- `SKL-STYLE` البصمة الأسلوبية للمؤلف

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-GDOCS` Google Docs — platform

## بوابات الجودة
QG3, QG5

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SED-1 | نسبة ملاحظات التحكيم المغلقة قبل QG5 | 100% |
| K-SED-2 | أخطاء لغوية مكتشفة بعد QG5 لكل 10 آلاف كلمة | <= 3 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
