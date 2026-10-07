<!-- GENERATED from agents/_specs/AG-RED.yaml by `rkpos generate` — do not edit by hand. -->
# الفريق الأحمر — Red Team Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-RED` |
| الإدارة | DEP-06 |
| التصنيف | متخصص (Specialist) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | Devil's Advocate Agent, Logical Consistency Agent |

## المهمة
محاولة هدم الحجة بصدق: تفنيدها، والبحث عن الأدلة المعارضة، وكشف التناقض والتحيز والقفزات المنطقية والسببية الزائفة والتعميم — ليخرج النص أصلب لا أضعف.

## المسؤوليات
- تفكيك الحجة إلى مقدمات ونتائج واختبار كل رابط
- طلب أدلة معارضة عبر AG-DSC وتقييمها
- كشف المغالطات والتحيز التأكيدي والتعميم
- اختبار الادعاءات السببية (بدائل، عوامل مربكة، اتجاه السببية)
- فحص الاتساق بين الفصول

## المهارات
- `SKL-REDTEAM` بروتوكول الفريق الأحمر
- `SKL-ARGMAP` رسم خرائط الحجاج
- `SKL-CAUSAL` الاستدلال السببي

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-OPENALEX` OpenAlex API — public_api
- `TL-S2` Semantic Scholar API — public_api

## بوابات الجودة
QG3

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-RED-1 | تحديات حرجة أغلقت قبل الاعتماد | 100% |
| K-RED-2 | عدد ملاحظات Red Team لكل فصل | متابعة الاتجاه |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
