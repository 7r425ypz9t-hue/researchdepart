<!-- GENERATED from agents/_specs/AG-SUP-EVD.yaml by `rkpos generate` — do not edit by hand. -->
# مشرف الأدلة — Evidence Supervisor

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-SUP-EVD` |
| الإدارة | DEP-11 |
| التصنيف | إشرافي (Supervisory) |
| المستوى | L4-Senior |
| فئة النموذج | T4-independent |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
الحكم على كفاية الأدلة وموثوقيتها وتوازنها قبل البناء عليها (QG1)، والتحقق من أن سجل الأدلة يغطي كل ادعاء جوهري في الفصل قبل انتقاله إلى التحرير.

## المسؤوليات
- قياس تغطية الأدلة لأسئلة البحث
- فحص توزيع المصادر على هرم الموثوقية
- كشف انحياز الانتقاء (مصادر في اتجاه واحد)
- إصدار قرار QG1 والمشاركة في QG4 من جهة الأدلة

## المهارات
- `SKL-CITEVERIFY` التحقق من الاستشهاد
- `SKL-FACTCHECK` تدقيق الوقائع
- `SKL-BIBLIOMETRIC` التحليل الببليومتري

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)
- `TL-ZOTERO` Zotero Web API — needs_account
- `TL-SQL` SQL Database — built_in (SQLite) / needs_install (PostgreSQL)

## بوابات الجودة
QG1, QG4

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-SEV-1 | نسبة الادعاءات الجوهرية المغطاة بدليل متحقق | >= 98% |
| K-SEV-2 | نسبة مصادر Tier1-2 في الحجج المركزية | >= 70% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
