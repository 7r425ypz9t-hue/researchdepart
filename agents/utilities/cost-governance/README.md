<!-- GENERATED from agents/_specs/AG-CST.yaml by `rkpos generate` — do not edit by hand. -->
# وكيل حوكمة الكلفة — Cost Governance Agent

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-CST` |
| الإدارة | DEP-10 |
| التصنيف | خدمي (Utility) |
| المستوى | L2-Associate |
| فئة النموذج | T1-economy |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
رصد كلفة الرموز وواجهات API والتخزين والخدمات لكل مشروع وفصل ووكيل، ومقارنتها بالحدود، والإنذار المبكر، واقتراح توجيه أوفر دون المساس بالجودة.

## المسؤوليات
- تجميع الكلفة من سجلات المحوّل (model adapter)
- حساب الكلفة لكل مشروع/فصل/وكيل/مرحلة
- إنذار عند 50% و75% و90% من الحد
- اقتراح إعادة توجيه نموذجي للمهام البسيطة

## المهارات
- `SKL-COSTTRACK` تتبع الكلفة

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-SQL` SQL Database — built_in (SQLite) / needs_install (PostgreSQL)
- `TL-GSHEETS` Google Sheets — platform

## بوابات الجودة
—

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-CST-1 | مشاريع تجاوزت الحد دون إنذار مسبق | 0 |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
