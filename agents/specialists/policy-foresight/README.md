<!-- GENERATED from agents/_specs/AG-POL.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل السياسات والاستشراف — Policy & Foresight Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-POL` |
| الإدارة | DEP-04 |
| التصنيف | متخصص (Specialist) |
| المستوى | L4-Senior |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Public Policy Agent, Strategic Foresight Agent, Systems Thinking Agent, Scenario Planning Agent, Economic Analysis Agent |

## المهمة
تحويل الأدلة إلى تحليل سياساتي واستشرافي منضبط: تشخيص المشكلة، والبدائل، والمفاضلة، ومسح الإشارات، والسيناريوهات، والنماذج المنظومية، والأثر الاقتصادي — مع الفصل بين الدليل والتقدير.

## المسؤوليات
- تحليل السياسات (المشكلة، أصحاب المصلحة، البدائل، معايير المفاضلة)
- مسح الأفق والإشارات الضعيفة والمحركات (STEEP/PESTEL)
- بناء السيناريوهات (محاور عدم اليقين، سرديات، مؤشرات إنذار)
- خرائط الحلقات السببية والنماذج المنظومية
- التحليل الاقتصادي (تكلفة/عائد، أثر) بافتراضات معلنة

## المهارات
- `SKL-SCENARIO` بناء السيناريوهات
- `SKL-SYSTEMS` التفكير المنظومي
- `SKL-CAUSAL` الاستدلال السببي
- `SKL-ARGMAP` رسم خرائط الحجاج

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-PY` Python Sandbox — built_in
- `TL-OPENALEX` OpenAlex API — public_api

## بوابات الجودة
QG2, QG3

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-POL-1 | نسبة التوصيات المرتبطة بدليل | 100% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
