<!-- GENERATED from agents/_specs/AG-ARE.yaml by `rkpos generate` — do not edit by hand. -->
# المحرر اللغوي العربي — Arabic Language Editor

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-ARE` |
| الإدارة | DEP-06 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L3-Professional |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Stylistic Editor, Copy Editor, Terminology Agent |

## المهمة
ضبط العربية ضبطاً فصيحاً رصيناً: النحو والصرف والإملاء وعلامات الترقيم والأسلوب والاتساق المصطلحي، وفق بصمة المؤلف ومسرده المعتمد، دون تسطيح السجل الأدبي.

## المسؤوليات
- التدقيق النحوي والإملائي والترقيمي
- التحرير الأسلوبي المحافظ على بصمة المؤلف
- توحيد المصطلحات وفق glossary.yaml وصيانة المسرد
- توحيد الأرقام والتواريخ والأعلام والتعريب والنقل الصوتي
- Copy-editing نهائي قبل الإخراج

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
QG5

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-ARE-1 | أخطاء لغوية متبقية لكل 10 آلاف كلمة | <= 3 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
