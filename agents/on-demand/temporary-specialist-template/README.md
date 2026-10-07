<!-- GENERATED from agents/_specs/AG-TMP.yaml by `rkpos generate` — do not edit by hand. -->
# قالب الوكيل المتخصص المؤقت — Temporary Specialist Agent (Template)

| الحقل | القيمة |
|---|---|
| المعرّف | `AG-TMP` |
| الإدارة | DEP-01 |
| التصنيف | عند الطلب (On-Demand) |
| المستوى | L3-Professional |
| فئة النموذج | T3-advanced |
| ضمن MVP | لا |
| نماذج التشغيل | B, C |
| يستوعب | — |

## المهمة
قالب يُنسخ لإنشاء متخصص مؤقت لمهمة محددة بعمر محدد، بصلاحيات دنيا، ثم يُقيَّم عند إغلاق المشروع لتقرير إلغائه أو ترقيته إلى وكيل دائم عبر اختبارات الانحدار.

## المسؤوليات
- {{DOMAIN_TASK}} — تُملأ عند الإنشاء
- تسليم مخرجاته عبر المنسق فقط
- كتابة تقرير ختامي يقيم الحاجة إلى الاستدامة

## المهارات
- (لا شيء)

## الأدوات
- `TL-FS` Repository File System — built_in
- `TL-MSG` Agent Message Bus — built_in
- `TL-AUDIT` Audit Logger — built_in
- `TL-LLM` Model Adapter Layer — built_in (adapter) + needs_account (provider keys)

## بوابات الجودة
—

## مؤشرات الأداء
| المعرّف | المؤشر | الهدف |
|---|---|---|
| K-TMP-1 | إنجاز المهمة ضمن العمر المحدد | 100% |

## الملفات
`agent.yaml` · `system_prompt.md` · `tools.yaml` · `permissions.yaml` · `memory.yaml` · `handoffs.yaml` · `tests.yaml`
