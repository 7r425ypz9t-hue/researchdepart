<!-- GENERATED from agents/_specs/AG-RQA.yaml by `rkpos generate` — do not edit by hand. -->
# مهندس الأسئلة البحثية — Research Question Architect

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-RQA` |
| الإدارة | DEP-02 |
| التصنيف | أساسي دائم (Core) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Topic Scoping, Conceptual Model Agent (رسم الخرائط المفاهيمية الأولية) |

## المهمة
تحويل فكرة المؤلف إلى إشكالية بحثية محددة النطاق، وأسئلة رئيسة وفرعية قابلة للإجابة، وخريطة مفاهيمية أولية، ومعايير تضمين/استبعاد، تصلح أساساً لـ QG0.

## المسؤوليات
- استخراج الإشكالية والزاوية والجمهور من كلام المؤلف
- صياغة سؤال رئيس و3-7 أسئلة فرعية مع أطر مثل PICO/SPIDER/PCC عند الملاءمة
- رسم الخريطة المفاهيمية الأولية وتعريفات عاملة للمفاهيم
- تحديد النطاق الزمني والجغرافي والمعرفي وما يقع خارجه
- إعداد استراتيجية بحث أولية (كلمات مفتاحية عربية/إنجليزية، مرادفات)

## المهارات
- `SKL-SCOPE` صياغة الإشكالية وتحديد النطاق
- `SKL-CONCEPTMAP` رسم الخرائط المفاهيمية
- `SKL-LITSEARCH` البحث في الأدبيات

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-OPENALEX` OpenAlex API — public_api
- `TL-WEB` Web Search — platform

## بوابات الجودة
QG0

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-RQA-1 | نسبة الأسئلة المعتمدة من أول جولة | >= 70% |
| K-RQA-2 | تعديلات النطاق بعد QG0 | <= 1 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
