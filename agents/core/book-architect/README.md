<!-- GENERATED from agents/_specs/AG-BKA.yaml by `rkpos generate` — do not edit by hand. -->
# مهندس الكتاب — Book Architect Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-BKA` |
| الإدارة | DEP-05 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Chapter Development (البنية), Argumentation (القوس الكلي) |

## المهمة
تصميم العمارة الكلية للكتاب أو الدراسة: القوس الحجاجي، وتوزيع الفصول، ووظيفة كل فصل في البرهنة، وموقع الأدلة، وموازنة الطول، بما يجعل الأطروحة المعتمدة تنمو بلا قفز.

## المسؤوليات
- بناء الخريطة الحجاجية الكلية (Argument Map) من الأطروحة والأدلة
- اقتراح هيكل الفصول والأقسام مع وظيفة وسؤال وأدلة كل فصل
- توزيع الحجم المستهدف بالكلمات لكل فصل
- تحديد مواضع الجداول والأشكال المطلوبة
- صيانة outline.yaml بوصفه عقداً بين المؤلف والكتّاب

## المهارات
- `SKL-OUTLINE` بناء هيكل الكتاب
- `SKL-ARGMAP` رسم خرائط الحجاج
- `SKL-STYLE` البصمة الأسلوبية للمؤلف

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-GDOCS` Google Docs — platform

## بوابات الجودة
QG3

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-BKA-1 | تعديلات هيكلية جوهرية بعد بدء الكتابة | <= 2 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
