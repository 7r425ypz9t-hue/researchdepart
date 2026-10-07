<!-- GENERATED from agents/_specs/AG-SUP-INT.yaml by `rkpos generate` — do not edit by hand. -->
# مشرف النزاهة — Integrity Supervisor

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SUP-INT` |
| الإدارة | DEP-11 |
| التصنيف | إشرافي (Supervisory) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
إصدار قرار QG4 المستقل بعد تقارير وكيل النزاهة ووكيل التدقيق: لا تلفيق، لا انتحال، لا خرق حقوق، لا نسبة خاطئة، وإفصاح سليم عن استخدام الذكاء الاصطناعي.

## المسؤوليات
- مراجعة تقرير AG-INT وتقرير AG-EVA معاً
- التحقق من سلامة وسوم الادعاءات وسجل الاقتباس الحرفي
- التحقق من أذونات الصور والجداول والاقتباسات الطويلة
- إصدار قرار QG4

## المهارات
- `SKL-RISKAUDIT` تقدير خطر الانتحال
- `SKL-RIGHTS` الحقوق والأذونات
- `SKL-CLAIMTAG` وسم الادعاءات

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-SIMCHECK` Similarity Check Service — needs_account

## بوابات الجودة
QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SIN-1 | مخالفات نزاهة اكتُشفت بعد النشر | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
